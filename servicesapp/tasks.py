import frappe
from frappe.utils import nowdate

ESCALATION_DOCTYPES = [
    "Instrument Application Master",
    "Installation Request Master",
    "Instrument Breakdown master",
    "Other Calls Issue Master",
]

def check_for_missed_calls():
    """
    Check for missed calls across ALL configured doctypes
    """
    for doctype_name in ESCALATION_DOCTYPES:
        process_overdue_calls(doctype_name)
    
    frappe.db.commit()

def process_overdue_calls(doctype_name):
    """Process overdue calls for a specific doctype"""
    
    try:
        # Find overdue calls
        overdue_calls = frappe.get_all(doctype_name, 
            filters={
                "call_schedule_date": ["<", nowdate()],
                "workflow_state": ["in", ["Open", ""]]
            }
        )

        for call in overdue_calls:
            try:
                # Update call status
                frappe.db.set_value(doctype_name, call.name, "call_status", "Assigned")
                
                doc = frappe.get_doc(doctype_name, call.name)
                
                # Set workflow state to Escalated (L1)
                doc.workflow_state = "Escalated (L1)"
                doc.flags.ignore_permissions = True
                doc.save()
                
                # Create approval entry
                create_approval_entry(doc)
                
            except Exception as e:
                frappe.log_error(
                    f"Failed to escalate {doctype_name} {call.name}: {str(e)}", 
                    "Escalation Error"
                )
    
    except Exception as e:
        frappe.log_error(
            f"Failed to process {doctype_name}: {str(e)}",
            "Escalation Error"
        )

def create_approval_entry(doc):
    """Create approval entry for escalated document"""
    
    # Fetch the approval policy for this doctype
    approval_policy = frappe.db.get_value(
        "Approval Policy",
        {"applies_to_doctype": doc.doctype},
        "name"
    )
    
    if not approval_policy:
        frappe.log_error(
            f"No approval policy found for {doc.doctype}. Skipping approval entry creation.",
            "Approval Policy Missing"
        )
        return
    
    approval_doc = frappe.get_doc({
        "doctype": "Approval Entry",
        "status": "Escalated to Manager",
        "applied_to_doctype": doc.doctype,
        "record": doc.name,
        "approval_policy": approval_policy,  # Now fetched dynamically
        "approval_entry": [{
            "action": "Approved", 
            "current_stage": "Open",
            "next_stage": "Escalated (L1)",
            "approver_user": "Administrator"
        }]
    })
    approval_doc.insert(ignore_permissions=True)