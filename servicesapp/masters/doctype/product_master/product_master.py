# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ProductMaster(Document):
    pass


import frappe
from collections import defaultdict
from datetime import datetime

import frappe

import frappe

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