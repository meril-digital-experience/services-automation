"""
Main approval/rejection endpoint for document workflows.

This module provides the primary API for approving or rejecting documents
that are in an approval workflow.

Key Responsibilities:
- Validating approval actions (Approved/Rejected)
- Verifying user authorization for the current approval stage
- Transitioning documents through multi-stage approval workflows
- Recording approval history with remarks

State Machine:
    Pending --> Stage 1 --> Stage 2 --> ... --> Approved
         |          |           |
         +----------+-----------+----------> Rejected

Usage:
    POST /api/method/master_data_suite.api.approval.approve.approve_document
    {
        "doctype": "Sales Order",
        "docname": "SO-0001",
        "action": "Approved",
        "remarks": "Budget approved"
    }
"""

import frappe

from servicesapp.overwrite.approval.helper.constants import VALID_APPROVAL_ACTIONS
from servicesapp.overwrite.approval.helper.entry import add_approve_entry
from servicesapp.overwrite.approval.helper.user import verify_approval_user
from servicesapp.overwrite.constants import ApprovalAction, ApprovalStatus
from servicesapp.overwrite.exceptions.approval import (
	ApprovalAlreadyCompleteError,
	ApprovalUnauthorizedError,
	NoApproverFoundError,
)
from servicesapp.overwrite.approval.utils.approval.entry import get_document as get_approval_entry_doc
from servicesapp.overwrite.approval.utils.approval.policy import _get_next_approval_user, get_current_stage
from servicesapp.overwrite.approval.utils.verify_user import verify_user_identity


def _validate_action(action: str) -> None:
	"""Validate that the action is either Approved or Rejected."""
	if action not in VALID_APPROVAL_ACTIONS:
		frappe.throw(f"Invalid action. Allowed actions are: {', '.join(VALID_APPROVAL_ACTIONS)}")


def _ensure_authorized_user(user_type: str, user_id: str) -> None:
	"""Ensure the current user is linked to an employee or distributor."""
	if not user_type or not user_id:
		raise ApprovalUnauthorizedError()


def _ensure_stage_approver(next_stage, action: str, next_approver) -> None:
	"""Ensure there is a valid approver for the next stage."""
	if action == ApprovalAction.APPROVED and next_stage and not next_approver:
		raise NoApproverFoundError(
			stage=next_stage.get("approval_stage_name", "Unknown"),
			role=next_stage.get("role", "Unknown"),
		)


def _ensure_not_already_approved(approval_entry_doc, doctype: str, docname: str) -> None:
	"""Ensure the document hasn't already been approved or rejected."""
	status = approval_entry_doc.get("status")
	if ApprovalStatus.is_terminal(status):
		entry_desc = approval_entry_doc.get("applied_to_doctype") or doctype
		entry_record = approval_entry_doc.get("record") or docname
		raise ApprovalAlreadyCompleteError(entry_desc, entry_record, status)


# master_data_suite.api.approval.approve.approve_document
@frappe.whitelist(methods=["POST"])
def approve_document(doctype: str, docname: str, action: str, remarks: str) -> None:
	_validate_action(action)
	is_approved = action == "Approved"

	user_type, user_id, user = verify_user_identity(user=frappe.session.user)
	_ensure_authorized_user(user_type, user_id)

	approval_entry_doc = get_approval_entry_doc(doctype, docname)
	approval_policy_doc = frappe.get_cached_doc("Approval Policy", approval_entry_doc.approval_policy)

	_ensure_not_already_approved(approval_entry_doc, doctype, docname)

	verify_approval_user(approval_policy_doc, approval_entry_doc, user_type, user_id, user)

	current_stage = get_current_stage(approval_entry_doc)

	if action == ApprovalAction.REJECTED:
		approval_entry_doc.db_set("status", ApprovalStatus.REJECTED)
		doctype_meta = frappe.get_meta(doctype)
		doc = frappe.get_doc(doctype, docname)

		if doctype_meta.has_field("status"):
			doc.status = ApprovalStatus.REJECTED

		add_approve_entry(
			approval_entry_doc=approval_entry_doc,
			next_approver=None,
			current_stage=current_stage,
			next_stage=None,
			action=action,
			remarks=remarks,
			user_id=user_id,
		)

		doc.save()

		return {
			"message": f"Document '{docname}' of type '{doctype}' has been {action.lower()} successfully."
		}

	next_approver, next_stage = _get_next_approval_user(current_stage, approval_entry_doc, user_type, user_id)

	_ensure_stage_approver(next_stage, action, next_approver)

	if not next_stage:
		approval_entry_doc.db_set("status", ApprovalStatus.APPROVED if is_approved else action)

	doctype_meta = frappe.get_meta(doctype)
	doc = frappe.get_doc(doctype, docname)

	if doctype_meta.has_field("status"):
		status_value = (
			ApprovalStatus.APPROVED
			if is_approved and not next_stage
			else next_stage.get("approval_stage_name")
			if next_stage
			else ApprovalStatus.PENDING
		)
		doc.status = status_value

	if doctype_meta.has_field("approval_remarks"):
		doc.approval_remarks = remarks

	add_approve_entry(
		approval_entry_doc=approval_entry_doc,
		next_approver=next_approver,
		current_stage=current_stage,
		next_stage=next_stage,
		action=action,
		remarks=remarks,
		user_id=user_id,
	)

	doc.save()

	return {"message": f"Document '{docname}' of type '{doctype}' has been {action.lower()} successfully."}
