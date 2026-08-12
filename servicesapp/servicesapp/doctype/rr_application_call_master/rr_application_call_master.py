# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from servicesapp.utils.assign_engineer import assign_engineer


class RRApplicationCallMaster(Document):
    pass
    def after_insert(self):
       assign_engineer(self)
       self.db_set("assigned_engineer", self.assigned_engineer)

    def autoname(self):
        last = frappe.db.sql("""
            SELECT name 
            FROM `tabRR Application Call Master` 
            WHERE name LIKE 'ARR%'
            ORDER BY CAST(SUBSTRING(name, 4) AS UNSIGNED) DESC 
            LIMIT 1
        """, as_dict=True)

        if last:
            last_num = int(last[0]["name"].replace("ARR", ""))
            new_num = last_num + 1
        else:
            new_num = 1

        self.name = f"ARR{str(new_num).zfill(10)}"
    
