import base64
import json
import mimetypes
import os
import smtplib
from contextlib import contextmanager
from dataclasses import dataclass
from email import encoders
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any

import frappe

from servicesapp.overwrite.approval.utils.notification import create_notification_log

Recipients = str | list[str] | None
AttachmentData = dict[str, Any] | str | Any
Attachments = AttachmentData | list[AttachmentData] | None


@dataclass
class EmailSettings:
	email_id: str = "noreply@merillife.com"
	smtp_server: str = "smtp.zeptomail.in"
	smtp_port: int = 465
	use_ssl: bool = True
	use_tls: bool = False
	password: str | None = None
	sender_name: str = "Meril"
	always_bcc: list[str] | None = None


@dataclass
class ProcessedAttachment:
	filename: str
	content: bytes
	content_type: str = "application/octet-stream"


class EmailSendingError(Exception):
	pass


def is_email_sending_suspended() -> bool:
	try:
		return bool(int(frappe.db.get_default("suspend_email_queue") or 0))
	except (ValueError, TypeError):
		return False


def normalize_recipients(recipients: Recipients) -> list[str]:
	if not recipients:
		return []

	if isinstance(recipients, str):
		recipients = [r.strip() for r in recipients.split(",")]

	return [str(r).strip() for r in recipients if r and str(r).strip()]


def _log_debug(message: str) -> None:
	frappe.logger("email").debug(message)


def _log_error(message: str, title: str = "Email Error") -> None:
	frappe.logger("email").error(message)
	frappe.log_error(frappe.get_traceback(), title)


def get_email_settings(email_id: str = "noreply@merillife.com") -> EmailSettings:
	settings = EmailSettings(email_id=email_id)

	try:
		email_account = frappe.get_doc("Email Account", {"email_id": email_id})

		settings.smtp_server = email_account.smtp_server or settings.smtp_server
		settings.smtp_port = email_account.smtp_port or settings.smtp_port
		settings.use_ssl = getattr(email_account, "use_ssl", True)
		settings.use_tls = getattr(email_account, "use_tls", False)
		settings.password = email_account.get_password()
		settings.sender_name = getattr(email_account, "sender_name", None) or "Meril"

		always_bcc = getattr(email_account, "always_bcc", None)
		if always_bcc:
			settings.always_bcc = normalize_recipients(always_bcc)

		_log_debug(f"Email settings loaded for {email_id}")

	except frappe.DoesNotExistError:
		_log_debug(f"Email account {email_id} not found, using defaults")
	except Exception as e:
		_log_error(f"Failed to load email settings for {email_id}: {e}")

	return settings


def render_email_template(template_name: str, context: dict[str, Any]) -> tuple[str, str]:
	try:
		template_data = frappe.db.get_value(
			"Email Template", template_name, ["subject", "response", "response_html"], as_dict=True
		)

		if not template_data:
			raise frappe.DoesNotExistError(f"Email Template '{template_name}' not found")

		subject = template_data.get("subject", "")
		response = template_data.get("response", "")

		empty_editor_content = '<div class="ql-editor read-mode"><p><br></p></div>'
		if response == empty_editor_content:
			response = template_data.get("response_html", "")

		rendered_subject = frappe.render_template(subject, context) if subject else ""
		rendered_message = frappe.render_template(response, context) if response else ""

		return rendered_subject, rendered_message

	except frappe.DoesNotExistError:
		raise
	except Exception as e:
		_log_error(
			f"Error rendering template {template_name}: {e}", f"Email Template Render Error: {template_name}"
		)
		return "Email Template Error", f"Failed to render email template: {e}"


def process_attachments(attachments: Attachments) -> list[ProcessedAttachment]:
	if not attachments:
		return []

	if isinstance(attachments, dict) or not isinstance(attachments, list):
		attachments = [attachments]

	processed = []

	for attachment in attachments:
		try:
			result = _process_single_attachment(attachment)
			if result:
				processed.append(result)
		except Exception as e:
			_log_debug(f"Failed to process attachment: {e}")

	return processed


def _process_single_attachment(attachment: AttachmentData) -> ProcessedAttachment | None:
	if isinstance(attachment, dict):
		content = attachment.get("fcontent") or attachment.get("content")
		filename = attachment.get("fname") or attachment.get("filename", "attachment")

		if content:
			if isinstance(content, str):
				try:
					content = base64.b64decode(content)
				except Exception:
					content = content.encode("utf-8")

			content_type, _ = mimetypes.guess_type(filename)
			return ProcessedAttachment(
				filename=filename, content=content, content_type=content_type or "application/octet-stream"
			)

	elif isinstance(attachment, str):
		if os.path.exists(attachment):
			with open(attachment, "rb") as f:
				content = f.read()

			filename = os.path.basename(attachment)
			content_type, _ = mimetypes.guess_type(filename)

			return ProcessedAttachment(
				filename=filename, content=content, content_type=content_type or "application/octet-stream"
			)

	elif hasattr(attachment, "file_name") and hasattr(attachment, "content"):
		content = attachment.content
		if isinstance(content, str):
			content = content.encode("utf-8")

		content_type, _ = mimetypes.guess_type(attachment.file_name)
		return ProcessedAttachment(
			filename=attachment.file_name,
			content=content,
			content_type=content_type or "application/octet-stream",
		)

	return None


def format_attachments_for_queue(attachments: list[ProcessedAttachment]) -> str | None:
	if not attachments:
		return None

	formatted = [
		{"fname": att.filename, "fcontent": base64.b64encode(att.content).decode("utf-8")}
		for att in attachments
	]

	return json.dumps(formatted) if formatted else None


def build_email_message(
	subject: str,
	body: str,
	to_emails: list[str],
	cc_emails: list[str],
	bcc_emails: list[str],
	settings: EmailSettings,
	attachments: list[ProcessedAttachment] | None = None,
) -> MIMEMultipart | EmailMessage:
	from_addr = formataddr((settings.sender_name, settings.email_id))

	if attachments:
		msg = MIMEMultipart()
		msg["Subject"] = subject
		msg["From"] = from_addr
		msg["To"] = ", ".join(to_emails)

		if cc_emails:
			msg["Cc"] = ", ".join(cc_emails)
		if bcc_emails:
			msg["Bcc"] = ", ".join(bcc_emails)

		msg.attach(MIMEText(body, "html"))

		for att in attachments:
			main_type, sub_type = att.content_type.split("/", 1)
			part = MIMEBase(main_type, sub_type)
			part.set_payload(att.content)
			encoders.encode_base64(part)
			part.add_header("Content-Disposition", f'attachment; filename="{att.filename}"')
			msg.attach(part)
	else:
		msg = EmailMessage()
		msg["Subject"] = subject
		msg["From"] = from_addr
		msg["To"] = ", ".join(to_emails)

		if cc_emails:
			msg["Cc"] = ", ".join(cc_emails)
		if bcc_emails:
			msg["Bcc"] = ", ".join(bcc_emails)

		msg.add_alternative(body, subtype="html")

	return msg


@contextmanager
def smtp_connection(settings: EmailSettings):
	server = None
	try:
		if settings.use_ssl:
			server = smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port)
		else:
			server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
			if settings.use_tls:
				server.starttls()

		if settings.password:
			server.login(settings.email_id, settings.password)

		yield server

	finally:
		if server:
			try:
				server.quit()
			except Exception:
				pass


def save_to_email_queue(
	msg: MIMEMultipart | EmailMessage,
	subject: str,
	to_emails: list[str],
	cc_emails: list[str],
	settings: EmailSettings,
	attachments: list[ProcessedAttachment] | None = None,
	status: str = "Not Sent",
) -> str | None:
	try:
		full_message = msg.as_string()

		email_queue = frappe.get_doc(
			{
				"doctype": "Email Queue",
				"subject": subject,
				"message": full_message,
				"status": status,
				"show_as_cc": ", ".join(cc_emails) if cc_emails else "",
				"sender": settings.email_id,
				"sender_full_name": settings.sender_name,
				"attachments": format_attachments_for_queue(attachments) if attachments else None,
			}
		)

		for recipient in to_emails:
			email_queue.append("recipients", {"recipient": recipient, "status": status})

		email_queue.flags.ignore_permissions = True
		email_queue.insert(ignore_permissions=True)

		_log_debug(f"Email Queue created: {email_queue.name} (status: {status})")
		return email_queue.name

	except Exception as e:
		_log_error(f"Failed to create Email Queue: {e}", "Email Queue Creation Error")
		return None


def send_via_smtp(
	subject: str,
	body: str,
	to_emails: list[str],
	cc_emails: list[str] | None = None,
	bcc_emails: list[str] | None = None,
	attachments: Attachments = None,
) -> bool:
	cc_emails = cc_emails or []
	bcc_emails = bcc_emails or []

	settings = get_email_settings()

	if not bcc_emails and settings.always_bcc:
		bcc_emails = settings.always_bcc
		_log_debug(f"Using always_bcc: {bcc_emails}")

	processed_attachments = process_attachments(attachments) if attachments else None

	msg = build_email_message(
		subject=subject,
		body=body,
		to_emails=to_emails,
		cc_emails=cc_emails,
		bcc_emails=bcc_emails,
		settings=settings,
		attachments=processed_attachments,
	)

	all_recipients = to_emails + cc_emails + bcc_emails

	if is_email_sending_suspended():
		_log_debug("Email sending suspended - saving to queue")
		save_to_email_queue(
			msg=msg,
			subject=subject,
			to_emails=to_emails,
			cc_emails=cc_emails,
			settings=settings,
			attachments=processed_attachments,
			status="Not Sent",
		)
		return True

	if not settings.password:
		raise EmailSendingError("Email password not configured in Email Account settings")

	_log_debug(f"Sending email - TO: {to_emails}, CC: {cc_emails}, BCC: {bcc_emails}")

	try:
		with smtp_connection(settings) as server:
			server.send_message(msg, to_addrs=all_recipients)

		_log_debug(f"Email sent successfully to {len(all_recipients)} recipients")

		save_to_email_queue(
			msg=msg,
			subject=subject,
			to_emails=to_emails,
			cc_emails=cc_emails,
			settings=settings,
			attachments=processed_attachments,
			status="Sent",
		)
		return True

	except smtplib.SMTPException as e:
		_log_error(f"SMTP error: {e}", "SMTP Send Error")

		save_to_email_queue(
			msg=msg,
			subject=subject,
			to_emails=to_emails,
			cc_emails=cc_emails,
			settings=settings,
			attachments=processed_attachments,
			status="Not Sent",
		)
		return False

	except Exception as e:
		_log_error(f"Failed to send email: {e}", "Email Send Error")

		save_to_email_queue(
			msg=msg,
			subject=subject,
			to_emails=to_emails,
			cc_emails=cc_emails,
			settings=settings,
			attachments=processed_attachments,
			status="Not Sent",
		)
		return False


def needs_custom_smtp(cc: Recipients, bcc: Recipients, attachments: Attachments) -> bool:
	if normalize_recipients(cc) or normalize_recipients(bcc) or attachments:
		return True

	try:
		email_account = frappe.get_doc("Email Account", {"email_id": "noreply@merillife.com"})
		if getattr(email_account, "always_bcc", None):
			return True
	except Exception:
		pass

	return False


def custom_sendmail(
	recipients: Recipients = None,
	subject: str | None = None,
	message: str | None = None,
	cc: Recipients = None,
	bcc: Recipients = None,
	attachments: Attachments = None,
	template: str | None = None,
	args: dict[str, Any] | None = None,
	**kwargs,
) -> None:
	args = args or {}

	if template:
		subject, message = render_email_template(template, args)
	elif args:
		if subject:
			subject = frappe.render_template(subject, args)
		if message:
			message = frappe.render_template(message, args)

	create_notification_log(recipients=recipients, subject=subject, message=message, **kwargs)

	to_emails = normalize_recipients(recipients)
	cc_emails = normalize_recipients(cc)
	bcc_emails = normalize_recipients(bcc)

	if not to_emails:
		_log_debug("No recipients specified - skipping email")
		return

	if not needs_custom_smtp(cc, bcc, attachments):
		frappe.sendmail(
			recipients=to_emails,
			subject=subject,
			message=message,
			delayed=is_email_sending_suspended(),
			**kwargs,
		)
		return

	send_now = kwargs.get("now", False)

	if send_now:
		send_via_smtp(
			subject=subject,
			body=message,
			to_emails=to_emails,
			cc_emails=cc_emails,
			bcc_emails=bcc_emails,
			attachments=attachments,
		)
	else:
		frappe.enqueue(
			method=send_via_smtp,
			subject=subject,
			body=message,
			to_emails=to_emails,
			cc_emails=cc_emails,
			bcc_emails=bcc_emails,
			attachments=attachments,
		)


def custom_send_mail(
	mail_template: str,
	recipient: Recipients,
	email_context: dict[str, Any] | None = None,
	cc_recepients: Recipients = None,
	**kwargs,
) -> None:
	custom_sendmail(
		recipients=recipient,
		cc=cc_recepients,
		template=mail_template,
		args=email_context,
		now=kwargs.get("now", True),
		**kwargs,
	)


@frappe.whitelist()
def toggle_sending(enable: str | int | bool) -> None:
	frappe.only_for("System Manager")
	frappe.db.set_default("suspend_email_queue", 0 if frappe.utils.cint(enable) else 1)


frappe.custom_sendmail = custom_sendmail
