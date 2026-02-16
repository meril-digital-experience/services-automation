import frappe

def service_engineer_filter(user, doctype):
    if not user:
        user = frappe.session.user

    # Administrator bypass
    if user == "Administrator":
        return ""

    roles = frappe.get_roles(user)

    # Only restrict Service Engineer
    if "Service Engineer" not in roles:
        return ""

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        "name"
    )

    if not employee:
        return "1=0"

    return f"`tab{doctype}`.assigned_engineer = '{employee}'"

# Wrapper Functions for Each Doctype
def instrument_application_permission(user):
    return service_engineer_filter(user, "Instrument Application Master")

def installation_request_permission(user):
    return service_engineer_filter(user, "Installation Request Master")

def instrument_breakdown_permission(user):
    return service_engineer_filter(user, "Instrument Breakdown Master")

def rr_application_call_permission(user):
    return service_engineer_filter(user, "RR Application Call Master")

def other_calls_issue_permission(user):
    return service_engineer_filter(user, "Other Calls Issue Master")