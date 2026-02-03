from collections.abc import Callable
from typing import Literal

import frappe
from werkzeug.exceptions import UnprocessableEntity

UserType = Literal["distributor", "employee"]


def _get_request_headers() -> dict:
	"""
	Retrieve normalized HTTP headers from `frappe.local.request` if available.

	Returns:
	    dict: A dictionary of lowercased header keys and their values.
	          Returns an empty dict if no valid request object or headers are found.
	"""
	request_obj = getattr(frappe.local, "request", None)
	if not request_obj or not hasattr(request_obj, "headers"):
		return {}
	return {k.lower(): v for k, v in (request_obj.headers or {}).items()}


def _verify_linked_user(
	user: str | None,
	doctype: str,
	expected_user_type: str,
	throw_exception: bool,
	error_message: str,
) -> tuple[str | None, str | None]:
	"""
	Internal helper to verify a DocType record (e.g., Distributor or Employee)
	linked to a given Frappe user.

	This supports optional header-based overrides for system integrations:
	  - **X-User-Id**: Overrides the user's record ID if valid.
	  - **X-User-Type**: Must match the expected user type.

	Args:
	    user (str | None): The Frappe user to verify. Defaults to the session user.
	    doctype (str): The DocType to check (e.g., "Distributor" or "Employee").
	    expected_user_type (str): The expected header user type key.
	    throw_exception (bool): If True, raises `UnprocessableEntity` when invalid.
	    error_message (str): Error message used in exceptions.

	Returns:
	    tuple[str | None, str | None]: (record_id, user) if verified,
	    otherwise `(None, None)` if not found and `throw_exception` is False.

	Raises:
	    UnprocessableEntity: If the user cannot be verified and `throw_exception` is True.
	"""
	user = user or frappe.session.user
	headers = _get_request_headers()

	header_user_id = headers.get("x-user-id")
	header_user_type = headers.get("x-user-type")

	# Header override if valid
	if header_user_id and header_user_type:
		if header_user_type == expected_user_type and frappe.db.exists(doctype, header_user_id):
			return header_user_id, user
		if throw_exception:
			raise UnprocessableEntity(error_message)

	# Normal (non-header) flow: check if user is linked to a record in doctype
	# Try to find a record in doctype where the user is linked
	# Assumes the link field is 'company_email' (adjust if needed)
	record_id = frappe.get_cached_value(doctype, {"company_email": user})
	if record_id:
		return record_id, user
	if throw_exception:
		raise UnprocessableEntity(error_message)

	return None, None


def verify_distributor(
	user: str | None = None, throw_exception: bool = True
) -> tuple[str | None, str | None]:
	"""
	Verify and return the Distributor record linked to a given user.

	Args:
	    user (str | None): Frappe user ID to verify. Defaults to session user.
	    throw_exception (bool): If True, raises an error when not found.

	Returns:
	    tuple[str | None, str | None]: (distributor_record_id, user) if found, otherwise None.

	Raises:
	    UnprocessableEntity: If Distributor not found and `throw_exception` is True.
	"""
	return _verify_linked_user(
		user=user,
		doctype="MDS Distributor",
		expected_user_type="distributor",
		throw_exception=throw_exception,
		error_message="Distributor not found",
	)


def verify_employee(user: str | None = None, throw_exception: bool = True) -> tuple[str | None, str | None]:
	"""
	Verify and return the Employee record linked to a given user.

	Args:
	    user (str | None): Frappe user ID to verify. Defaults to session user.
	    throw_exception (bool): If True, raises an error when not found.

	Returns:
	    tuple[str | None, str | None]: (employee_record_id, user) if found, otherwise None.

	Raises:
	    UnprocessableEntity: If Employee not found and `throw_exception` is True.
	"""
	return _verify_linked_user(
		user=user,
		doctype="Employee",
		expected_user_type="employee",
		throw_exception=throw_exception,
		error_message="Employee not found",
	)


def verify_user_identity(
	user: str | None = None,
	order: tuple[UserType, ...] = ("distributor", "employee"),
	throw_exception: bool = True,
) -> tuple[UserType, str, str]:
	"""
	Resolve and return the business identity of the current user.

	Attempts to match the user against the provided `order` of user types
	(Distributor → Employee by default). Returns the first valid match.

	Args:
	    user (str | None): Frappe user ID to check. Defaults to session user.
	    order (tuple[UserType, ...]): Sequence of user types to check in order.
	    throw_exception (bool): If True, raises error if no linked identity is found.

	Returns:
	    tuple[UserType, str, str] | None: `(user_type, record_id, user)` if verified.
	    Returns `None` if not found and `throw_exception` is False.

	Raises:
	    UnprocessableEntity: If no linked record found and `throw_exception` is True.
	"""
	resolvers: dict[str, Callable[[], tuple[str | None, str | None]]] = {
		"distributor": lambda: verify_distributor(user, throw_exception=False),
		"employee": lambda: verify_employee(user, throw_exception=False),
	}

	for user_type in order:
		resolver = resolvers.get(user_type)
		if not resolver:
			continue

		record_id, user = resolver()
		if record_id:
			return user_type, record_id, user

	if throw_exception:
		raise UnprocessableEntity("No linked Distributor or Employee found for this user")

	return None, None, None
