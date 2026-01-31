# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ProductMaster(Document):
    pass
#    def before_insert(self):
        # 1. Take the Product Name (e.g., "GlucoQuant A1C HBA1C Analyzer")
#        name = self.product_name
        
        # 2. Extract initials (e.g., GQAHA)
        # We split by space and take the first letter of each word
#        initials = "".join([word[0].upper() for word in name.split() if word])
        
        # 3. Handle the suffix/counter
        # We check how many products already start with these initials
#        existing_count = frappe.db.count("Product", {
#            "product_code": ["like", f"{initials}%"]
#        })
        
        # 4. Construct the code (e.g., GQAHA-01)
        # :02d ensures it stays as -01, -02, etc.
#        self.product_code = f"{initials}-{existing_count + 1:02d}"