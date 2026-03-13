"""
Custom exceptions for the approval workflow.

These exceptions provide specific, actionable error messages that help
developers and users understand what went wrong and how to fix it.

Usage:
    from master_data_suite.exceptions.approval import (
        ApprovalUnauthorizedError,
        ApprovalNotFoundError,
    )

    # Raise with context
    raise ApprovalUnauthorizedError(
        stage="Manager Review",
        required_role="Manager"
    )

    # Or use simple form
    raise ApprovalNotFoundError("Sales Order", "SO-0001")
"""

import frappe


class ApprovalError(frappe.ValidationError):
	"""
	Base exception for all approval-related errors.

	Inherit from this class to create specific approval exceptions.
	This allows catching all approval errors with a single except clause.

	Example:
	    try:
	        approve_document(...)
	    except ApprovalError as e:
	        # Handle any approval-related error
	        log_error(e)
	"""

	pass


class ApprovalNotFoundError(ApprovalError):
	"""
	Raised when no approval entry exists for a document.

	This typically means:
	- The document doesn't have an active approval workflow
	- The approval entry was deleted
	- The doctype/docname combination is incorrect

	Attributes:
	    doctype: The DocType that was searched.
	    docname: The document name that was searched.
	"""

	def __init__(self, doctype: str, docname: str):
		self.doctype = doctype
		self.docname = docname
		message = (
			f"No approval entry found for {doctype} '{docname}'. "
			"Ensure the document has an active approval workflow configured."
		)
		super().__init__(message)


class ApprovalAlreadyCompleteError(ApprovalError):
	"""
	Raised when attempting to act on a completed approval.

	Once a document is Approved or Rejected, no further actions can be taken.
	This error prevents double-approval or modification of finalized workflows.

	Attributes:
	    doctype: The DocType of the document.
	    docname: The document name.
	    status: The current terminal status (Approved or Rejected).
	"""

	def __init__(self, doctype: str, docname: str, status: str):
		self.doctype = doctype
		self.docname = docname
		self.status = status
		message = (
			f"Cannot modify approval for {doctype} '{docname}'. "
			f"The document has already been {status.lower()}."
		)
		super().__init__(message)


class ApprovalUnauthorizedError(ApprovalError):
	"""
	Raised when a user is not authorized to approve at the current stage.

	This can happen when:
	- The user doesn't have the required role
	- The user is not in the reporting hierarchy of the document owner
	- The user has already approved and cannot approve again

	Attributes:
	    stage: The approval stage name (if available).
	    required_role: The role required for this stage (if available).
	"""

	def __init__(self, stage: str | None = None, required_role: str | None = None):
		self.stage = stage
		self.required_role = required_role

		if stage and required_role:
			message = (
				f"You are not authorized to approve at stage '{stage}'. "
				f"This stage requires an approver with the '{required_role}' role."
			)
		elif stage:
			message = f"You are not authorized to approve at stage '{stage}'."
		else:
			message = (
				"You are not authorized to perform this approval action. "
				"Please check if you have the required role or are in the correct reporting hierarchy."
			)
		super().__init__(message)


class NoApproverFoundError(ApprovalError):
	"""
	Raised when no valid approver can be found for a stage.

	This typically means:
	- No employee with the required role exists in the reporting hierarchy
	- The hierarchy traversal reached the maximum depth without finding an approver
	- The approval policy configuration is incorrect

	Attributes:
	    stage: The approval stage name.
	    role: The role that was being searched for.
	"""

	def __init__(self, stage: str, role: str):
		self.stage = stage
		self.role = role
		message = (
			f"No valid approver found for stage '{stage}'. "
			f"Ensure an employee with the '{role}' role exists in the reporting hierarchy."
		)
		super().__init__(message)
