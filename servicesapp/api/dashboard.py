import frappe
import json

@frappe.whitelist()
def get_engineer_count(filters=None):

    user = frappe.session.user

    # Parse filters (comes as JSON string)
    if filters:
        if isinstance(filters, str):
            filters = json.loads(filters)
        doctype = filters.get("doctype")
    else:
        return {"value": 0, "fieldtype": "Int"}

    if not doctype:
        return {"value": 0, "fieldtype": "Int"}

    # Admin bypass
    if user == "Administrator":
        count = frappe.db.count(doctype)
        return {
            "value": count,
            "fieldtype": "Int",
            "route": ["List", doctype]
        }

    roles = frappe.get_roles(user)

    if "Service Engineer" not in roles:
        return {"value": 0, "fieldtype": "Int"}

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        "name"
    )

    if not employee:
        return {"value": 0, "fieldtype": "Int"}

    count = frappe.db.count(
        doctype,
        {"assigned_engineer": employee}
    )

    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", doctype],
        "route_options": {
            "assigned_engineer": employee
        }
    }