"""
Approval workflow status and action constants.

This module provides centralized definitions for all status values
and actions used in the approval workflow. Using these constants
instead of string literals ensures consistency and makes refactoring easier.

Status Flow Diagram:
    +---------+
    | Pending |
    +----+----+
         |
         v
    +----------+     +----------+     +----------+
    | Stage 1  | --> | Stage 2  | --> | Stage N  |
    +----+-----+     +----+-----+     +----+-----+
         |               |                 |
         |               |                 v
         |               |           +----------+
         |               |           | Approved |
         |               |           +----------+
         |               |
         +---------------+----------------------+
                                                |
                                                v
                                          +----------+
                                          | Rejected |
                                          +----------+

Usage:
    from master_data_suite.constants.approval_status import (
        ApprovalStatus,
        ApprovalAction,
        VALID_APPROVAL_ACTIONS,
    )

    # Check if status is terminal
    if ApprovalStatus.is_terminal(doc.status):
        print("Workflow complete")

    # Validate action
    if action not in VALID_APPROVAL_ACTIONS:
        raise ValueError("Invalid action")
"""


class ApprovalStatus:
	"""
	Valid status values for Approval Entry documents.

	Status values represent the current state of a document in the approval workflow.
	A document starts as "Pending", moves through stage names during approval,
	and ends as either "Approved" or "Rejected".

	Attributes:
	    PENDING: Initial status when approval entry is created.
	    APPROVED: Terminal status indicating successful approval.
	    REJECTED: Terminal status indicating the document was rejected.
	"""

	PENDING = "Pending"
	APPROVED = "Approved"
	REJECTED = "Rejected"

	@classmethod
	def terminal_statuses(cls) -> set:
		"""
		Get status values that indicate workflow completion.

		Returns:
		    set: A set containing APPROVED and REJECTED statuses.
		"""
		return {cls.APPROVED, cls.REJECTED}

	@classmethod
	def is_terminal(cls, status: str) -> bool:
		"""
		Check if a status indicates the workflow is complete.

		Args:
		    status: The status value to check.

		Returns:
		    bool: True if the status is terminal (Approved or Rejected).
		"""
		return status in cls.terminal_statuses()


class ApprovalAction:
	"""
	Valid actions that can be taken on an approval.

	Actions represent what a user does when they act on an approval request.
	Currently, only "Approved" and "Rejected" are valid actions.

	Attributes:
	    APPROVED: Action to approve and move to the next stage.
	    REJECTED: Action to reject and terminate the workflow.
	"""

	APPROVED = "Approved"
	REJECTED = "Rejected"


# List of valid approval actions for validation
# This maintains backward compatibility with existing code that imports VALID_APPROVAL_ACTIONS
VALID_APPROVAL_ACTIONS = [ApprovalAction.APPROVED, ApprovalAction.REJECTED]

# Set of terminal statuses for quick lookup
TERMINAL_STATUSES = ApprovalStatus.terminal_statuses()
