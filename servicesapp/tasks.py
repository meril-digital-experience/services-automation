import frappe
from frappe.utils import nowdate

def check_for_missed_calls():
    # 1. Find overdue calls
    overdue_calls = frappe.get_all("Instrument Application Master", 
        filters={
            "call_schedule_date": ["<", nowdate()],
            "workflow_state": ["in", ["Open", ""]]
        }
    )

    for call in overdue_calls:
        frappe.db.set_value("Instrument Application Master", call.name, "call_status", "Assigned")
        
        doc = frappe.get_doc("Instrument Application Master", call.name)
        
        # WORKFLOW trigger
        # pushes the state from Open to Escalated (L1)
        doc.workflow_action = "Auto Escalate"
        doc.save(ignore_permissions=True)
        
        #APPROVAL ENTRY
        approval_doc = frappe.get_doc({
            "doctype": "Approval Entry",
            "status": "Escalated to Manager",
            "applied_to_doctype": "Instrument Application Master",
            "record": doc.name,
            "approval_policy": "AP-000001", #policy id
            "approval_entry": [{
                "action": "Approved", 
                "current_stage": "Open",
                "next_stage": "Escalated (L1)",
                "approver_user": "Administrator"
            }]
        })
        approval_doc.insert(ignore_permissions=True)
    
    frappe.db.commit()