# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from servicesapp.utils import assign_engineer

class InstrumentBreakdownmaster(Document):
    def after_insert(self):
        assign_engineer(self)
        self.db_set("assigned_engineer", self.assigned_engineer)


def get_permission_query_conditions(user):
    if not user: 
        user = frappe.session.user 
    
    
    if "System Manager" in frappe.get_roles(user):
        return ""
    
    
    return f"assigned_engineer = '{user}'"