"""
User validation helpers for approval workflows.

This module provides functions to:
- Validate if a user can approve at the current stage
- Find the next approver in the hierarchy
- Verify user authorization for approval actions
"""

import frappe

from servicesapp.overwrite.exceptions.approval import ApprovalUnauthorizedError
from servicesapp.overwrite.approval.utils.approval.user import get_user_for_approval


def validate_approval_entry(approval_record, approval_entry_doc, user_type, user_id, user) -> bool:
	"""
	Validate if a user can approve the current approval entry.

	Args:
	    approval_record: The approval stage configuration from the policy.
	    approval_entry_doc: The Approval Entry document being validated.
	    user_type: The type of user ("employee" or "distributor").
	    user_id: The ID of the current user's linked employee/distributor.
	    user: The Frappe user object.

	Returns:
	    bool: True if the user can approve, False otherwise.
	"""
	approver_type = approval_record.get("approver_type")

	if approver_type.lower().strip() == "role":
		expected_role = approval_record.get("role")
		actual_role = approval_entry_doc.get("next_approval_role")
		if expected_role != actual_role:
			return False

	if user_type == "employee":
		expected_employee = approval_entry_doc.get("next_approver")
		return expected_employee == user_id

	return False


# Note: for now this is only handling employee type users and from hierarchy type approvals
def get_next_approval_user(
	next_stage,
	user_type,
	user_id,
) -> str | None:
	if not next_stage:
		return None
	next_approval_role = next_stage.get("role")

	# Decide based on user type
	if user_type == "employee":
		return get_user_for_approval(user_id, next_approval_role, check_cur_user=True)

	return None


def verify_approval_user(approval_policy_doc, approval_entry_doc, user_type, user_id, user) -> None:
	"""
	Verify that the current user is authorized to approve at the current stage.

	This function checks:
	1. That approval stages are configured for the policy
	2. That the current stage exists in the policy
	3. That the user matches the expected approver for this stage

	Args:
	    approval_policy_doc: The Approval Policy document.
	    approval_entry_doc: The Approval Entry document.
	    user_type: The type of user ("employee" or "distributor").
	    user_id: The ID of the current user's linked employee/distributor.
	    user: The Frappe user object.

	Raises:
	    frappe.ValidationError: If no approval stages are configured.
	    ApprovalUnauthorizedError: If the user is not authorized to approve.
	"""
	next_approval_stage = approval_entry_doc.get("next_approval_stage")
	approvals = approval_policy_doc.get("approvals") or []

	if not approvals:
		frappe.throw("No approval stages are configured for this policy.")

	approval_record = next(
		(item for item in approvals if int(item.get("idx")) == int(next_approval_stage)), None
	)

	if not approval_record or not validate_approval_entry(
		approval_record, approval_entry_doc, user_type, user_id, user
	):
		# Provide context about which stage and role is expected
		stage_name = approval_record.get("approval_stage_name") if approval_record else None
		required_role = approval_record.get("role") if approval_record else None
		raise ApprovalUnauthorizedError(stage=stage_name, required_role=required_role)
