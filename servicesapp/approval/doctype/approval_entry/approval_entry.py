# Copyright (c) 2025, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType


class ApprovalEntry(Document):
	def autoname(self):
		prefix = f"{self.approval_policy}-AE-"
		ApprovalEntryTable = DocType("Approval Entry")

		# Fetch names that match the prefix
		names = (
			frappe.qb.from_(ApprovalEntryTable)
			.select(ApprovalEntryTable.name)
			.where(ApprovalEntryTable.name.like(f"{prefix}%"))
		).run(pluck=True)

		numbers = [int(name.split("-")[-1]) for name in names if name.split("-")[-1].isdigit()]

		last_number = max(numbers) if numbers else 0
		next_number = last_number + 1
		self.name = f"{prefix}{str(next_number).zfill(6)}"

	def _update_next_approver_details(self):
		# Use the actual child table fieldname: 'approvals'
		rows = self.get("approval_entry") or []
		if not rows:
			return

		last = rows[-1]

		# Only set when present & changed
		nxt_approver = last.get("next_approver", "")
		if nxt_approver and nxt_approver != self.get("next_approver"):
			self.db_set("next_approver", nxt_approver, update_modified=False)
			employee_name, company_email = frappe.get_cached_value(
				"Employee", nxt_approver, ["employee_name", "company_email"]
			)
			self.db_set("next_approver_name", employee_name, update_modified=False)
			self.db_set("next_approver_user", company_email, update_modified=False)
		elif not nxt_approver:
			self.db_set("next_approver", "", update_modified=False)
			self.db_set("next_approver_name", "", update_modified=False)
			self.db_set("next_approver_user", "", update_modified=False)

		nxt_stage = last.get("next_stage", "")
		if nxt_stage and nxt_stage != self.get("next_approval_stage"):
			self.db_set("next_approval_stage", nxt_stage, update_modified=False)
		elif not nxt_stage:
			self.db_set("next_approval_stage", "", update_modified=False)

		nxt_role = last.get("next_approver_role", "")
		if nxt_role and nxt_role != self.get("next_approval_role"):
			self.db_set("next_approval_role", nxt_role, update_modified=False)
		elif not nxt_role:
			self.db_set("next_approval_role", "", update_modified=False)

	def _update_previous_approver_details(self):
		# Use the actual child table fieldname: 'approvals'
		rows = self.get("approval_entry") or []
		if not rows:
			return

		last = rows[-1]

		# Only set when present & changed
		prv_approver = last.get("approved_by", "")
		if prv_approver and prv_approver != self.get("previous_approver"):
			self.db_set("previous_approver", prv_approver, update_modified=False)
			employee_name, company_email = frappe.get_cached_value(
				"Employee", prv_approver, ["employee_name", "company_email"]
			)
			self.db_set("previous_approver_name", employee_name, update_modified=False)
		elif not prv_approver:
			self.db_set("previous_approver", "", update_modified=False)
			self.db_set("previous_approver_name", "", update_modified=False)

		prv_remarks = last.get("remarks", "")
		if prv_remarks and prv_remarks != self.get("previous_approver_remarks"):
			self.db_set("previous_approver_remarks", prv_remarks, update_modified=False)
		elif not prv_remarks:
			self.db_set("previous_approver_remarks", "", update_modified=False)

	def after_insert(self):
		self._update_next_approver_details()

	def on_update(self):
		self._update_next_approver_details()
		self._update_previous_approver_details()
