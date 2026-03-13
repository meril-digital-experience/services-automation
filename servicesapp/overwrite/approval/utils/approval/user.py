"""
Employee hierarchy traversal for approval workflows.

This module provides utilities to find the appropriate approver
by traversing the employee reporting hierarchy.

The hierarchy is based on the `reporting_head` field in Employee,
where each employee may have a manager above them.

Example hierarchy:
    CEO (role: Director)
      └── Manager (role: Manager)
            └── Employee (role: Staff)

When looking for an approver with role "Manager" starting from "Employee",
this module will traverse up to find "Manager".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import frappe

if TYPE_CHECKING:
	from frappe.model.document import Document

# Maximum levels to traverse up the reporting hierarchy.
# Prevents infinite loops from circular reporting relationships.
MAX_HIERARCHY_DEPTH = 8


def get_user_for_approval(
	name: str | None,
	role: str,
	depth: int = 0,
	check_cur_user: bool = False,
) -> Document | None:
	"""
	Traverse the employee reporting hierarchy to find an approver with the specified role.

	This function recursively walks up the reporting chain (via `reporting_head` field)
	until it finds an employee with the matching role, or reaches the maximum depth.

	Args:
	    name (str): The Employee ID to start traversal from.
	    role (str): The role the approver must have (e.g., "Manager", "Director").
	    depth (int): Current recursion depth (internal use, do not set).
	    check_cur_user (bool): If True, check if the starting employee has the role.
	        Set to True when the initiating user might also be the approver.

	Returns:
	    frappe._dict | None: The Employee document if an approver is found,
	        None if no approver with the role exists within MAX_HIERARCHY_DEPTH levels.

	Example:
	    >>> approver = get_user_for_approval("EMP-001", "Manager")
	    >>> if approver:
	    ...     print(f"Found approver: {approver.name}")
	"""
	if depth > MAX_HIERARCHY_DEPTH or not name:
		return None

	employee = frappe.get_cached_doc("Employee", name)

	if (check_cur_user or depth > 0) and employee.get("role") == role:
		return employee

	return get_user_for_approval(employee.get("reporting_head", None), role, depth + 1)
