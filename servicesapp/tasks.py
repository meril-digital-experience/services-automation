import frappe
from frappe.utils import nowdate, add_days, now_datetime, add_to_date

ESCALATION_DOCTYPES = [
    "Instrument Application Master",
    "Installation Request Master",
    "Instrument Breakdown Master",
    "Other Calls Issue Master",
]

def check_for_missed_calls():
    """
    Check for missed calls and handle multi-level escalation
    """
    for doctype_name in ESCALATION_DOCTYPES:
        process_initial_escalation(doctype_name)
        process_higher_level_escalation(doctype_name)
    
    frappe.db.commit()

def process_initial_escalation(doctype_name):
    """
    Escalate calls that are 24+ hours overdue and still in Open state
    """
    
    try:
        cutoff_date = add_days(nowdate(), -1)
        
        # Pending/Assigned status
        overdue_calls = frappe.get_all(doctype_name, 
            filters={
                "call_schedule_date": ["<", cutoff_date],
                "workflow_state": ["in", ["Open", ""]],
                "call_status": ["in", ["Pending", "Assigned"]],
                "escalation_level": ["in", [0, None]]
            }
        )
        
        # In Progress status
        overdue_in_progress = frappe.get_all(doctype_name,
            filters={
                "in_progress_call_schedule_date": ["<", cutoff_date],
                "workflow_state": ["in", ["Open", ""]],
                "call_status": "In Progress",
                "escalation_level": ["in", [0, None]]
            }
        )
        
        all_overdue = overdue_calls + overdue_in_progress

        for call in all_overdue:
            try:
                doc = frappe.get_doc(doctype_name, call.name)
                
                # Get assigned engineer (Employee name)
                engineer_name = doc.assigned_engineer
                if not engineer_name:
                    frappe.log_error(f"No engineer assigned to {doc.name}", "Escalation Error")
                    continue
                
                # Get engineer's employee record
                engineer = frappe.db.get_value("Employee", 
                    engineer_name,
                    ["reports_to", "user_id"], 
                    as_dict=True
                )
                
                if not engineer or not engineer.reports_to:
                    frappe.log_error(
                        f"Engineer {engineer_name} has no reporting manager set",
                        "Escalation Error"
                    )
                    continue
                
                # Get reporting manager's details
                manager = frappe.db.get_value("Employee",
                    engineer.reports_to,
                    ["user_id", "name"],
                    as_dict=True
                )
                
                if not manager or not manager.user_id:
                    frappe.log_error(
                        f"Manager {engineer.reports_to} has no user_id set",
                        "Escalation Error"
                    )
                    continue
                
                # Update document for L1 escalation
                doc.workflow_state = "Escalated"
                doc.escalation_level = 1
                doc.escalated_on = now_datetime()
                doc.current_approver = manager.user_id
                doc.flags.ignore_permissions = True
                doc.save()
                
                # Send notification
                send_escalation_notification(doc, manager.user_id, 1)
                
                # Create approval entry
                create_approval_entry(doc)
                
            except Exception as e:
                frappe.log_error(
                    f"Failed to escalate {doctype_name} {call.name}: {str(e)}", 
                    "L1 Escalation Error"
                )
    
    except Exception as e:
        frappe.log_error(
            f"Failed to process initial escalation for {doctype_name}: {str(e)}",
            "Escalation Error"
        )

def process_higher_level_escalation(doctype_name):
    """
    Auto-escalate up the reporting chain if no action taken in 24 hours
    """
    
    try:
        cutoff_datetime = add_to_date(now_datetime(), hours=-24)
        
        escalated_calls = frappe.get_all(doctype_name,
            filters={
                "workflow_state": "Escalated",
                "escalated_on": ["<", cutoff_datetime],
                "escalation_level": [">", 0]
            },
            fields=["name", "escalation_level", "current_approver"]
        )
        
        for call in escalated_calls:
            try:
                doc = frappe.get_doc(doctype_name, call.name)
                
                # Get current approver's employee record by user_id
                current_approver_employee = frappe.db.get_value("Employee",
                    {"user_id": doc.current_approver},
                    ["reports_to", "name"],
                    as_dict=True
                )
                
                if not current_approver_employee:
                    continue
                
                # Check if current approver is HOD (FIXED)
                is_hod_role = frappe.db.exists("Has Role", {
                    "parent": doc.current_approver,
                    "role": "HOD"
                })
                
                # Convert to boolean - exists() returns record name if found, None if not
                is_hod = is_hod_role is not None
                
                if is_hod:
                    # Already at HOD level, don't escalate further
                    continue
                
                # Get next level manager
                if not current_approver_employee.reports_to:
                    # No higher reporting manager, stop here
                    continue
                
                next_manager = frappe.db.get_value("Employee",
                    current_approver_employee.reports_to,
                    ["user_id", "name"],
                    as_dict=True
                )
                
                if not next_manager or not next_manager.user_id:
                    continue
                
                # Escalate to next level
                next_level = doc.escalation_level + 1
                
                doc.workflow_state = "Escalated"
                doc.escalation_level = next_level
                doc.escalated_on = now_datetime()
                doc.current_approver = next_manager.user_id
                doc.flags.ignore_permissions = True
                doc.save()
                
                send_escalation_notification(doc, next_manager.user_id, next_level)
                
            except Exception as e:
                frappe.log_error(
                    f"Failed to escalate {doctype_name} {call.name} to higher level: {str(e)}",
                    "Higher Level Escalation Error"
                )
    
    except Exception as e:
        frappe.log_error(
            f"Failed to process higher level escalation for {doctype_name}: {str(e)}",
            "Escalation Error"
        )

def send_escalation_notification(doc, approver_user, level):
    """Send escalation email to the appropriate approver"""
    
    frappe.sendmail(
        recipients=[approver_user],
        sender="noreply@merillife.com",
        subject=f"Service Call Escalated - Level {level}",
        message=f"""
        <div style="font-family: sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h2 style="color: #d9534f;">Escalation Alert (Level {level})</h2>
            <p>Dear Manager,</p>
            <p>This is an automated notification from the <b>Service Management System</b> regarding an escalated call.</p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>Document Type:</b></td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{doc.doctype}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>Document ID:</b></td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{doc.name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>Escalation Level:</b></td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">Level {level}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>Scheduled Date:</b></td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{doc.call_schedule_date}</td>
                </tr>
            </table>

            <p>This call has been escalated to you for review. Please take appropriate action.</p>

            <div style="margin-top: 25px;">
                <a href="{frappe.utils.get_url_to_form(doc.doctype, doc.name)}" 
                   style="background-color: #007bff; color: white; padding: 12px 20px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                   Open Document
                </a>
            </div>
            
            <p style="font-size: 12px; color: #777; margin-top: 30px;">
                This is a system-generated email.
            </p>
        </div>
        """
    )

def create_approval_entry(doc):
    """Create approval entry for escalated document"""
    
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
        "approval_policy": approval_policy,
        "approval_entry": [{
            "action": "Approved", 
            "current_stage": "Open",
            "next_stage": "Escalated",
            "approver_user": doc.current_approver
        }]
    })
    approval_doc.insert(ignore_permissions=True)