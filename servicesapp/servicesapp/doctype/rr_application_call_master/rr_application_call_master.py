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
        last = frappe.get_all(
            "RR Application Call Master",
            fields=["name"],
            order_by="name desc",
            limit=1
        )

        if last:
            last_num = int(last[0]["name"].replace("ARR", ""))
            new_num = last_num + 1
        else:
            new_num = 1

        self.name = f"ARR{str(new_num).zfill(10)}"
    
