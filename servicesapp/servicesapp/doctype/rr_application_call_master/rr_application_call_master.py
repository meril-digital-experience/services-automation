# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from servicesapp.utils import assign_engineer

class RRApplicationCallMaster(Document):
    pass
    #def after_insert(self):
     #   assign_engineer(self)
      #  self.db_set("assigned_engineer", self.assigned_engineer)
    
