# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Employee(Document):
	pass

@frappe.whitelist()
def create_user_from_employee(employee_name):
    emp = frappe.get_doc("Employee", employee_name)

    if not emp.company_email:
        frappe.throw("Company Email is required to create User")

    if emp.user_id:
        frappe.throw("User already linked with this Employee")

    email = emp.company_email.strip().lower()

    # Check if user already exists
    if frappe.db.exists("User", email):
        emp.user_id = email
        emp.save(ignore_permissions=True)
        return email

    # Create user
    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "enabled": 1,
        "send_welcome_email": 1
    })

    user.insert(ignore_permissions=True)

    # Assign role
    if emp.role:
        user.add_roles(emp.role)

    # Link back to employee
    emp.user_id = user.name
    emp.save(ignore_permissions=True)

    frappe.db.commit()

    return user.name
  
    def validate(self):
        # re-calculates the total every time the document is saved
        if self.assigned_calls:
            self.total_calls = len(self.assigned_calls)
        else:
            self.total_calls = 0
