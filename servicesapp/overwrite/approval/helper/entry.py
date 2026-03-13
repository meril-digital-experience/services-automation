"""
Helper functions for adding approval history entries.

This module provides the `add_approve_entry` function which records
each approval/rejection action in the Approval Entry's history.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Union

from servicesapp.overwrite.constants.approval_status import ApprovalStatus

if TYPE_CHECKING:
	from frappe.model.document import Document


def _determine_next_status(action: str, next_stage: dict | None) -> str:
	"""
	Determine the approval entry status after an action.

	Args:
	    action: The action taken ("Approved" or "Rejected").
	    next_stage: The next stage dict, or None if this is the final approval.

	Returns:
	    The new status value for the Approval Entry.
	"""
	if action == ApprovalStatus.REJECTED:
		return ApprovalStatus.REJECTED
	if next_stage:
		return next_stage.get("approval_stage_name")
	return ApprovalStatus.APPROVED


def add_approve_entry(
	approval_entry_doc: Document,
	next_approver: str | Document | None,
	current_stage: dict | None,
	next_stage: dict | None,
	action: str,
	remarks: str,
	user_id: str,
) -> None:
	"""
	Record an approval action in the Approval Entry's history.

	This function:
	1. Determines the new status based on the action and next stage
	2. Creates a history row with all relevant details
	3. Appends it to the approval_entry child table
	4. Saves the Approval Entry document

	Status Determination Logic:
	- If action is "Rejected" -> status = "Rejected"
	- If next_stage exists -> status = next_stage's name (e.g., "Manager Review")
	- If no next_stage (final approval) -> status = "Approved"

	Args:
	    approval_entry_doc: The Approval Entry document to update.
	    next_approver: Employee document of the next approver (or None).
	    current_stage: Dict with current stage info (must have "idx" key).
	    next_stage: Dict with next stage info (or None if final approval).
	    action: The action taken ("Approved" or "Rejected").
	    remarks: Comments from the approver.
	    user_id: Employee ID of the person taking the action.
	"""
	if isinstance(next_approver, str):
		next_approver_name = next_approver
	elif next_approver:
		next_approver_name = next_approver.name
	else:
		next_approver_name = None

	approval_entry_doc.status = _determine_next_status(action, next_stage)
	approval_entry_item = {
		"current_stage": current_stage.get("idx") if current_stage else None,
		"next_stage": next_stage.get("idx") if next_stage else None,
		"approved_by": user_id,
		"next_approver": next_approver_name,
		"action": action,
		"remarks": remarks,
		"status": next_stage.get("approval_stage_name") if next_stage else "",
		"next_approver_role": next_stage.get("role") if next_stage else None,
	}
	approval_entry_doc.append("approval_entry", approval_entry_item)
	approval_entry_doc.save(ignore_permissions=True)
