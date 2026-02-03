import frappe


def get_all_reporting_employees(
	employee_id: str,
	role: str | None = None,
	search: str | None = None,
	include_self: bool = False,
) -> list[frappe._dict]:
	"""Fetch enabled Employees reporting (directly/indirectly) to `employee_id`.

	If `role` is provided, filters by that role. Otherwise, returns employees with all roles.
	Optional `search` narrows the flat result using case-insensitive LIKE on `name` and `employee_name`.
	If `include_self` is True, includes the employee's own data in the result.
	"""
	if not employee_id:
		return []

	search_text = f"%{search.strip()}%" if search else None
	visited_heads: set[str] = set()

	def _collect_reports(head_id: str) -> list[frappe._dict]:
		if not head_id or head_id in visited_heads:
			return []

		visited_heads.add(head_id)

		filters = {"reporting_head": head_id, "enabled": 1}

		or_filters = {}
		if search_text:
			or_filters = {"name": ("like", search_text), "employee_name": ("like", search_text)}

		reports = frappe.get_all(
			"Employee",
			filters=filters,
			or_filters=or_filters,
			fields=["name", "employee_name", "role", "reporting_head", "company_email"],
		)

		result: list[frappe._dict] = []
		for report in reports:
			result.append(report)
			result.extend(_collect_reports(report.name))
		return result

	result = _collect_reports(employee_id)

	if include_self:
		self_data = frappe.get_all(
			"Employee",
			filters={"name": employee_id, "enabled": 1},
			fields=["name", "employee_name", "role", "reporting_head", "company_email"],
		)
		if self_data:
			result.insert(0, self_data[0])

	if role:
		return [emp for emp in result if emp.role == role]
	return result
