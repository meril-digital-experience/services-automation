# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Employee(Document):
    def validate(self):
        # re-calculates the total every time the document is saved
        if self.assigned_calls:
            self.total_calls = len(self.assigned_calls)
        else:
            self.total_calls = 0