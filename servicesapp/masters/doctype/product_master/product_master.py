# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from collections import defaultdict
from datetime import datetime

class ProductMaster(Document):
    pass

@frappe.whitelist()
def get_user_monthly_assigned_calls():
    user = frappe.session.user

    # Get Employee linked to this user
    employee = frappe.get_value(
        "Employee",
        {"company_email": user},
        "name"
    )

    if not employee:
        return {}

    doctypes = [
        "Instrument Application Master",
        "Installation Request Master",
        "Instrument Breakdown Master",
        "RR Application Call Master",
        "Other Calls Issue Master"
    ]

    result = {}

    for dt in doctypes:
        records = frappe.get_all(
            dt,
            filters={
                "assigned_engineer": employee,
                "call_status": "Assigned"
            },
            fields=["call_schedule_date"]
        )

        for row in records:
            if not row.call_schedule_date:
                continue

            month_key = row.call_schedule_date.strftime("%B %Y")

            if month_key not in result:
                result[month_key] = {}

            if dt not in result[month_key]:
                result[month_key][dt] = 0

            result[month_key][dt] += 1

    return result


@frappe.whitelist()
def get_monthly_call_status_trend():

    doctypes = [
        "Instrument Application Master",
        "Installation Request Master",
        "Instrument Breakdown Master",
        "RR Application Call Master",
        "Other Calls Issue Master"
    ]

    result = defaultdict(lambda: {
        "Assigned": 0,
        "In Progress": 0,
        "Finished": 0
    })

    for dt in doctypes:

        records = frappe.get_all(
            dt,
            fields=["call_schedule_date", "call_status"],
            filters={
                "docstatus": ["!=", 2]
            }
        )

        for r in records:
            if not r.call_schedule_date:
                continue

            month_key = getdate(r.call_schedule_date).replace(day=1)
            month_str = month_key.strftime("%Y-%m-01")

            status = (r.call_status or "").strip()

            if status in ["Assigned", "In Progress", "Finished"]:
                result[month_str][status] += 1

    final_result = {}

    for month, statuses in result.items():
        final_result[month] = {
            "Assigned": statuses.get("Assigned", 0),
            "In Progress": statuses.get("In Progress", 0),
            "Finished": statuses.get("Finished", 0),
        }

    frappe.response["message"] = dict(sorted(final_result.items()))

