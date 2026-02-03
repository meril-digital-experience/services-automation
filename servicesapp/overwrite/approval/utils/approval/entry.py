"""
Approval Entry CRUD operations.

This module provides utilities for creating and retrieving Approval Entry documents.
An Approval Entry is the runtime tracking record for a document going through
the approval workflow.

Key Fields in Approval Entry:
- status: Current state (Pending, stage name, Approved, Rejected)
- approval_policy: Link to the policy governing this workflow
- applied_to_doctype: The DocType being approved (e.g., "Sales Order")
- record: The specific document name (e.g., "SO-0001")
- next_approver: Employee ID of the person who should approve next
- approval_entry: Child table containing the approval history

Lifecycle:
    1. Document created with matching Approval Policy
    2. create_document() creates Approval Entry with first stage
    3. Each approval adds a row to approval_entry child table
    4. Final approval sets status to "Approved"
    5. Any rejection sets status to "Rejected"
"""

import frappe

from servicesapp.overwrite.approval.helper.entry import add_approve_entry
from servicesapp.overwrite.approval.utils.approval.policy import _get_next_approval_user, get_current_stage


def get_document(doctype: str, docname: str):
	"""
	Retrieve the Approval Entry document linked to the given DocType and record.

	Args:
	    doctype: The DocType of the referenced document (e.g., "Sales Order").
	    docname: The name (ID) of the referenced document (e.g., "SO-0001").

	Returns:
	    The Approval Entry document if found, or None if no approval entry exists.

	Example:
	    >>> entry = get_document("Sales Order", "SO-0001")
	    >>> if entry:
	    ...     print(f"Status: {entry.status}")
	    ... else:
	    ...     print("No approval workflow for this document")
	"""
	# Attempt to find the Approval Entry that references this document
	approval_entry_name = frappe.get_value(
		"Approval Entry",
		{"applied_to_doctype": doctype, "record": docname},
		"name",
	)

	if not approval_entry_name:
		return None  # Return None for consistency (not empty list)

	# Fetch the Approval Entry document
	return frappe.get_cached_doc("Approval Entry", approval_entry_name)


def create_document(policy, doctype, docname) -> frappe._dict:
	"""
	Create an Approval Entry document for a source document.

	This function initializes the approval workflow by:
	1. Determining the first approval stage from the policy
	2. Finding the initial approver based on hierarchy reference
	3. Creating the Approval Entry with "Pending" status
	4. Adding the first approval history row
	5. Updating the source document's status field (if it exists)

	Args:
	    policy (frappe._dict): The matched Approval Policy document.
	    doctype (str): The DocType of the source document (e.g., "Sales Order").
	    docname (str): The name of the source document (e.g., "SO-0001").

	Returns:
	    frappe._dict: The newly created Approval Entry document.

	Note:
	    The function uses `hierarchy_reference_field` from the policy to determine
	    which employee field on the source document to use for finding the approver.
	    For example, if hierarchy_reference_field is "owner_employee", the function
	    will look up that employee and traverse their reporting hierarchy.
	"""
	first_approver_line_item = get_current_stage(approval_policy=policy.name)
	doc_hierarchy_fieldname = policy.get("hierarchy_reference_field", "")
	hierarchy_user_doc_id = frappe.get_cached_value(doctype, docname, doc_hierarchy_fieldname)
	current_stage_stub = frappe._dict(
		{
			"idx": (first_approver_line_item.get("idx") - 1) if first_approver_line_item else 0,
		}
	)

	next_approver_doc = None
	resolved_stage = None
	if hierarchy_user_doc_id:
		next_approver_doc, resolved_stage = _get_next_approval_user(
			current_stage_stub,
			user_type="employee",
			user_id=hierarchy_user_doc_id,
			approval_policy=policy.name,
		)

	if resolved_stage:
		first_approver_line_item = resolved_stage

	# Create the Approval Entry document
	entry_doc = frappe.get_doc(
		{
			"doctype": "Approval Entry",
			"approval_policy": policy.name,
			"applied_to_doctype": doctype,
			"record": docname,
			"status": "Pending",
		}
	)
	entry_doc.insert(ignore_permissions=True)

	# Add the first approval entry row using add_approve_entry
	add_approve_entry(
		approval_entry_doc=entry_doc,
		next_approver=next_approver_doc,
		current_stage=current_stage_stub,
		next_stage=first_approver_line_item,
		action="",
		remarks="",
		user_id="",
	)
	entry_doc.reload()

	doctype_meta = frappe.get_meta(doctype)
	if doctype_meta.has_field("status"):
		frappe.db.set_value(doctype, docname, "status", entry_doc.status)

	return entry_doc
