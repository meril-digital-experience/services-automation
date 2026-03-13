# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days, date_diff 

class ContractMaster(Document):
    
    @frappe.whitelist()
    def calculate_pm_dates(self):
        if not (self.contract_start_date and self.contract_end_date and self.pm_frequency_period): #checks if values are filled
            frappe.throw("Please ensure Start Date, End Date, and Frequency are filled.")

        pm_count = int(''.join(filter(str.isdigit, self.pm_frequency_period))) #extract pm count
        
        total_days = date_diff(self.contract_end_date, self.contract_start_date) #total days
        
        interval = total_days / pm_count
        
        for i in range(1, pm_count + 1):
            field_name = f"{i}_pm_date" 
            
            days_to_add = interval * i
            scheduled_date = add_days(self.contract_start_date, int(days_to_add))
            
            self.db_set(field_name, scheduled_date)
            
        self.notify_update() 
        return True

    @frappe.whitelist()
    def generate_pm_calls(self):
        pm_date_fields = [
            "1_pm_date",
            "2_pm_date",
            "3_pm_date",
            "4_pm_date",
            "5_pm_date",
            "6_pm_date",
            "7_pm_date",
            "8_pm_date",
            "9_pm_date",
            "10_pm_date",
            "11_pm_date",
            "12_pm_date",
        ]

        created = 0

        for field in pm_date_fields:
            pm_date = self.get(field)
            if not pm_date:
                continue

            # Optional: avoid duplicates
            exists = frappe.db.exists(
                "PM Frequency Master",
                {
                    "contract": self.name,
                    "call_schedule_date": pm_date
                }
            )

            if exists:
                continue

            pm_doc = frappe.new_doc("PM Frequency Master")
            pm_doc.asset_no = self.asset_no
            pm_doc.contract_master_name = self.name
            pm_doc.call_schedule_date = pm_date
            pm_doc.contract_start_date = self.contract_start_date
            pm_doc.contract_end_date = self.contract_end_date
            pm_doc.insert(ignore_permissions=True)

            created += 1

        frappe.db.commit()

        return created

    def on_submit(self):
        self.update_asset_master_contract_details()

    def update_asset_master_contract_details(self):
        if not self.asset_no:
            return

        if frappe.db.exists(
            "Contract Master",
            {"asset_no": self.asset_no, "name": ["!=", self.name]}
        ):
            frappe.throw("Contract already exists for this Asset")

        asset_name = frappe.db.get_value(
            "Asset Master",
            {"asset_no": self.asset_no},
            "name"
        )

        if not asset_name:
            frappe.throw(
                f"Asset Master not found for Asset No: {self.asset_no}"
            )

        frappe.db.set_value(
            "Asset Master",
            asset_name,
            {
                "contract_type": self.contract_type,
                "contract_start_date": self.contract_start_date,
                "contract_end_date": self.contract_end_date,
            },
            update_modified=True
        )
