import frappe

from servicesapp.overwrite.approval.utils.user import get_all_reporting_employees
from servicesapp.overwrite.approval.utils.verify_user import verify_employee


# TODO: currently getting it by role only, need to enhance it to get by reporting hierarchy dynamically
# master_data_suite.api.approval.employee.get_reporting_employee_by_role
@frappe.whitelist()
def get_reporting_employee_by_role(
	role: str, employee_id: str | None = None, search: str | None = None
) -> dict:
	"""Fetch and return a list of all enabled Employees."""
	user = frappe.session.user
	if not employee_id:
		employee_id, user = verify_employee(user=user)

	employees = get_all_reporting_employees(employee_id, role, search)
	return {"status": "success", "data": employees}
