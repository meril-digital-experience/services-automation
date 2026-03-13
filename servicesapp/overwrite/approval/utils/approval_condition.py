import frappe
from frappe.model.db_query import DatabaseQuery


def get_condition_based_approvers(
    policy_name: str,
    stage_row
) -> list[str]:
    """
    Returns list of Employee IDs allowed to approve
    based on Approval Conditions + Role
    """

    if not stage_row.based_on_condition:
        return []

    if stage_row.approver_type != "Role" or not stage_row.role:
        return []

    policy = frappe.get_doc("Approval Policy", policy_name)

    if not policy.filters_json:
        return []

    filters = frappe.parse_json(policy.filters_json)

    employee_query = DatabaseQuery("Employee")

    conditions = []
    for f in filters:
        _, field, operator, value = f
        conditions.append([field, operator, value])

    employees = employee_query.execute(
        fields=["name", "user_id"],
        filters=conditions,
        as_list=False
    )

    if not employees:
        return []

    employee_names = [e["name"] for e in employees]

    role_users = frappe.get_all(
        "Has Role",
        filters={
            "role": stage_row.role,
            "parenttype": "User"
        },
        pluck="parent"
    )

    if not role_users:
        return []

    valid_employees = frappe.get_all(
        "Employee",
        filters={
            "name": ["in", employee_names],
            "user_id": ["in", role_users]
        },
        pluck="name"
    )

    return valid_employees