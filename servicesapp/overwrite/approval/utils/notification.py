from typing import Any

import frappe

Recipients = str | list[str] | None


def normalize_recipients(recipients: Recipients) -> list[str]:
	if not recipients:
		return []
	if isinstance(recipients, str):
		return [r.strip() for r in recipients.split(",") if r.strip()]
	return [str(r).strip() for r in recipients if r and str(r).strip()]


def create_notification_log(
	recipients: Recipients = None, subject: str | None = None, message: str | None = None, **kwargs
) -> list[Any]:
	recipient_list = normalize_recipients(recipients)

	if not recipient_list:
		return []

	notification_type = kwargs.get("type", "Alert")
	document_type = kwargs.get("document_type")
	document_name = kwargs.get("document_name")
	from_user = kwargs.get("from_user", frappe.session.user)

	valid_recipients = frappe.get_all("User", filters={"name": ["in", recipient_list]}, pluck="name")

	invalid_recipients = set(recipient_list) - set(valid_recipients)
	if invalid_recipients:
		frappe.log_error(
			f"Skipped notifications for non-existent users: {', '.join(invalid_recipients)}",
			"Notification Log Creation",
		)

	created_logs = []

	for recipient in valid_recipients:
		try:
			notification_doc = frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": subject,
					"type": notification_type,
					"document_type": document_type,
					"document_name": document_name,
					"for_user": recipient,
					"from_user": from_user,
					"email_content": message,
				}
			)
			notification_doc.insert(ignore_permissions=True)
			created_logs.append(notification_doc)
		except Exception as e:
			frappe.log_error(
				f"Failed to create notification for {recipient}: {e}", "Notification Log Creation"
			)

	return created_logs


def create_simple_notification(user: str, subject: str, message: str) -> list[Any]:
	return create_notification_log(recipients=user, subject=subject, message=message)


def create_document_notification(
	recipients: Recipients, subject: str, message: str, doc_type: str, doc_name: str
) -> list[Any]:
	return create_notification_log(
		recipients=recipients,
		subject=subject,
		message=message,
		document_type=doc_type,
		document_name=doc_name,
		type="Alert",
	)


def create_bulk_notification(user_list: list[str], subject: str, message: str) -> list[Any]:
	return create_notification_log(recipients=user_list, subject=subject, message=message)
