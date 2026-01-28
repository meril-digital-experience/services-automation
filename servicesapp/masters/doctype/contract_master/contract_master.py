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