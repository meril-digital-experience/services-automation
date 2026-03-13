"""
Custom exceptions for master_data_suite.

This module provides domain-specific exceptions that give better
context than generic Frappe errors.
"""

from helpdesk.exceptions.approval import (
	ApprovalAlreadyCompleteError,
	ApprovalError,
	ApprovalNotFoundError,
	ApprovalUnauthorizedError,
	NoApproverFoundError,
)

__all__ = [
	"ApprovalAlreadyCompleteError",
	"ApprovalError",
	"ApprovalNotFoundError",
	"ApprovalUnauthorizedError",
	"NoApproverFoundError",
]
