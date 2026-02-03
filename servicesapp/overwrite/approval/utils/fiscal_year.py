import frappe


def get_current_fiscal_year():
	return frappe.get_cached_value("MDS Fiscal Year", {"current_year": 1}, "fiscal_year")
