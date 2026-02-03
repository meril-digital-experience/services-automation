import frappe
from frappe import _


def api_response(
	data=None, message="Success", success=True, status_code=200, error=None, total_count=None, **kwargs
):
	"""
	Standard API response wrapper.

	Args:
		data (dict | list | None): Main data payload
		message (str): Human-readable message
		success (bool): Indicates success or failure
		status_code (int): HTTP status code
		error (dict | None): Error details for failed responses
		total_count (int | None): Optional total count for list APIs
		**kwargs: Additional metadata if needed

	Returns:
		dict: Standardized API response
	"""

	# frappe.local might not be available when called from background jobs or tests
	if getattr(frappe.local, "response", None) is not None:
		frappe.local.response["http_status_code"] = status_code

	response = {
		"success": success,
		"message": message,
		"data": data if data is not None else {},
	}

	if error:
		response["error"] = error

	if total_count is not None:
		response["total_count"] = total_count

	# Add any additional metadata
	if kwargs:
		response.update(kwargs)

	return response


def success_response(data=None, message="Success", total_count=None, status_code=200, **kwargs):
	"""
	Convenience helper for successful API responses. If total_count is None it is
	omitted; explicit values (even 0) are returned unchanged.
	"""

	return api_response(
		data=data, message=message, success=True, status_code=status_code, total_count=total_count, **kwargs
	)


def error_response(message="Error", error=None, status_code=400, **kwargs):
	"""
	For validation errors, permission errors, server errors, etc.
	"""
	return api_response(
		data=None,
		message=message,
		success=False,
		status_code=status_code,
		error=error or {"type": "ValidationError"},
		**kwargs,
	)
