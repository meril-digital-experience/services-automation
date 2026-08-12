# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from servicesapp.utils.assign_engineer import assign_engineer

class InstrumentApplicationMaster(Document):
    def after_insert(self):
        # assigning engineer
        assign_engineer(self)
        self.db_set("assigned_engineer", self.assigned_engineer)

    def autoname(self):
        last = frappe.db.sql("""
            SELECT name 
            FROM `tabInstrument Application Master` 
            WHERE name LIKE 'INSAPP%'
            ORDER BY CAST(SUBSTRING(name, 7) AS UNSIGNED) DESC 
            LIMIT 1
        """, as_dict=True)

        if last:
            last_num = int(last[0]["name"].replace("INSAPP", ""))
            new_num = last_num + 1
        else:
            new_num = 1

        self.name = f"INSAPP{str(new_num).zfill(7)}"

