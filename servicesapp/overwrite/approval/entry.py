"""
API endpoints for creating and checking approval entries.

This module provides endpoints for:
- Creating new approval entries when documents are submitted
- Checking if a document has an active approval workflow
"""

import frappe

from servicesapp.overwrite.constants.approval_status import TERMINAL_STATUSES
from servicesapp.overwrite.approval.utils.approval.entry import create_document
from servicesapp.overwrite.approval.utils.approval.policy import (
	get_approval_policy_multiple_condition,
	has_active_policy_for_doctype,
)


@frappe.whitelist()
def create_approval_entry(doctype: str, docname: str | int):
	if not doctype or not docname:
		frappe.throw("Doctype and Document name must be provided.")

	if not frappe.db.exists(doctype, docname):
		frappe.throw(f"Document '{docname}' of type '{doctype}' does not exist.")

	if not has_active_policy_for_doctype(doctype):
		return

	approval_policy = get_approval_policy_multiple_condition(doctype, docname)

	if approval_policy:
		create_document(approval_policy, doctype, docname)


@frappe.whitelist()
def has_enabled_approval_policy_and_entry(doctype: str, docname: str) -> bool:
	"""Return True if there is an enabled approval policy tied to the DocType
	and at least one non-approved approval entry for the given document.
	"""

	if not doctype or not docname:
		return False

	# First check if the DocType has an active approval policy
	if not has_active_policy_for_doctype(doctype):
		return False

	# Fetch all approval entries tied to this document
	entry_statuses = frappe.get_all(
		"Approval Entry",
		fields=["status"],
		filters={
			"applied_to_doctype": doctype,
			"record": docname,
		},
		pluck="status",
	)

	if not entry_statuses:
		return True

	return all(status in TERMINAL_STATUSES for status in entry_statuses)


# @frappe.whitelist()
# def can_approve(doctype: str, docname: str | int) -> bool:
# 	"""Return True if the current user has permission to approve the given document.

# 	This function checks if:
# 	1. An active approval entry exists for the document
# 	2. The approval entry is not in a terminal status (Approved/Rejected)
# 	3. The current user is the designated next approver

# 	Args:
# 	    doctype: The DocType of the document (e.g., "Sales Order").
# 	    docname: The document name (e.g., "SO-0001").

# 	Returns:
# 	    bool: True if the current user can approve, False otherwise.
# 	"""
# 	if not doctype or not docname:
# 		return False

# 	# Get the approval entry for this document
# 	approval_entry = frappe.get_value(
# 		"Approval Entry",
# 		{"applied_to_doctype": doctype, "record": docname},
# 		["name", "status", "next_approver", "next_approver_user"],
# 		as_dict=True,
# 	)

# 	# No approval entry exists for this document
# 	if not approval_entry:
# 		return False

# 	# Document is already approved or rejected (terminal status)
# 	if approval_entry.status in TERMINAL_STATUSES:
# 		return False

# 	# No next approver assigned
# 	if not approval_entry.next_approver and not approval_entry.next_approver_user:
# 		return False

# 	# Get the current user's linked employee
# 	current_user = frappe.session.user
# 	employee_id = frappe.get_value(
# 		"Employee",
# 		{"company_email": current_user},
# 		"name",
# 	)

# 	# User is not linked to an employee
# 	if not employee_id:
# 		return False

# 	# Check if the current user's employee matches the next approver
# 	return approval_entry.next_approver_user == current_user


@frappe.whitelist()
def can_approve(doctype: str, docname: str | int) -> bool:
    if not doctype or not docname:
        return False

    docname = str(docname)
    current_user = frappe.session.user

    frappe.logger().info(
        "🔥 can_approve | doctype=%s | docname=%s | user=%s",
        doctype, docname, current_user
    )

    approval_entry = frappe.get_value(
        "Approval Entry",
        {
            "applied_to_doctype": doctype,
            "record": docname,
        },
        [
            "name",
            "status",
            "next_approver",
            "next_approver_user",
        ],
        as_dict=True,
    )

    if not approval_entry:
        return False

    if approval_entry.status in TERMINAL_STATUSES:
        return False

    # USER-BASED approval (simplest + recommended)
    if approval_entry.next_approver_user:
        return approval_entry.next_approver_user == current_user

    # EMPLOYEE-BASED fallback
    employee_id = frappe.get_value(
        "Employee",
        {"user_id": current_user},
        "name",
    )

    if not employee_id:
        return False

    return approval_entry.next_approver == employee_id
