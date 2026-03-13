"""
Auth API Module

This module provides REST API endpoints for authentication and default data
retrieval in the Master Data Suite application.

API Endpoints:
- get_user_details: Get current logged-in user information
- get_default_details: Get default fiscal year and month data for app initialization
"""

import frappe

from servicesapp.overwrite.approval.utils.response import success_response


# master_data_suite.api.approval.auth.get_user_details
@frappe.whitelist()
def get_user_details() -> dict:
	"""
	Fetch and return details of the currently logged-in user.

	API Path: master_data_suite.api.approval.auth.get_user_details

	Returns:
		dict: Success response containing:
			- full_name: User's full name
			- user_image: URL to user's profile image
			- email: User's email address
			- employee: Employee document if linked, otherwise None

	Example:
		>>> frappe.call("master_data_suite.api.approval.auth.get_user_details")
	"""
	user = frappe.get_cached_doc("User", frappe.session.user)
	employee = (
		frappe.get_cached_doc("Employee", {"company_email": user.name})
		if frappe.db.exists("Employee", {"company_email": user.name})
		else None
	)
	user_details = {
		"full_name": user.full_name,
		"user_image": user.user_image,
		"email": user.name,
		"employee": employee,
	}
	return {"status": "success", "data": user_details}


# master_data_suite.api.approval.auth.get_default_details
@frappe.whitelist()
def get_default_details() -> dict:
	"""
	Get default application data including fiscal years and months.

	API Path: master_data_suite.api.approval.auth.get_default_details

	This endpoint returns essential reference data needed for app initialization,
	including the relevant fiscal years (current, previous, upcoming) and all
	enabled months.

	Returns:
		dict: Success response containing:
			- fiscal_year_details: List of enabled MDS Fiscal Year documents where
				current_year=1 OR upcoming_year=1 OR previous_year=1
			- month_details: List of all enabled MDS Month documents ordered by month_number

	Example:
		>>> frappe.call("master_data_suite.api.approval.auth.get_default_details")

	Note:
		This API is typically called during app startup to populate dropdowns
		and set default values for fiscal year and month selections.
	"""
	default_data = {
		"fiscal_year_details": frappe.get_all(
			"MDS Fiscal Year",
			filters={"enabled": 1},
			or_filters={
				"current_year": 1,
				"upcoming_year": 1,
				"previous_year": 1,
			},
			fields=["*"],
		),
		"month_details": frappe.get_all(
			"MDS Month", filters={"enabled": 1}, order_by="fiscal_order", fields=["*"]
		),
	}

	return success_response(data=default_data)
