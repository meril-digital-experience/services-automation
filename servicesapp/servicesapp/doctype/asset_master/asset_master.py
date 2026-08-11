# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import random

class AssetMaster(Document):

	def before_insert(self):
		if not self.asset_name or "new-asset-master" in self.asset_name:
			from servicesapp.servicesapp.doctype.asset_master.asset_master import get_asset_name
			self.asset_name = get_asset_name(self.product_name)

	def before_save(self):
		if not self.serial_no and self.product_name:
			product_short_code = frappe.db.get_value("Product Master", self.product_name, "product_short_code")
			if product_short_code:
				import re
				import random
				import string
				short_code = re.sub(r'[^A-Za-z0-9]', '', product_short_code)[:3].upper()
				remaining_length = 9 - len(short_code)
				if remaining_length > 0:
					random_part = ''.join(random.choices(string.digits, k=remaining_length))
					self.serial_no = short_code + random_part
				else:
					self.serial_no = short_code


@frappe.whitelist()
def get_asset_name(product_name):
    if not product_name:
        return None

    product = frappe.db.get_value( "Product Master", product_name, "client_name", as_dict=True)

    if not product or not product.client_name:
        return None

    company_short = frappe.db.get_value( "Company", product.client_name, "company_short_form")

    if not company_short:
        return None

    random_part = random.randint(10000, 99999)
    return f"{company_short.upper()}00{random_part}"
