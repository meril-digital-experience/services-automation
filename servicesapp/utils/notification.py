import frappe
from frappe import _

def create_notification_log(recipients=None, subject=None, message=None, **kwargs):
    """
    Create notification logs for specified recipients
    
    Args:
        recipients (str/list): User ID(s) to send notification to. Can be single user or list of users
        subject (str): Subject/title of the notification
        message (str): Message content of the notification
        **kwargs: Additional parameters like document_type, document_name, type, etc.
    
    Returns:
        list: List of created notification log documents
    """
    # if not recipients:
    #     frappe.throw("Recipients parameter is required")
    
    # if not subject:
    #     frappe.throw("Subject parameter is required")
    
    # Ensure recipients is a list
    if isinstance(recipients, str):
        recipients = [recipients]
    
    # Default values
    notification_type = kwargs.get("type", "Alert")
    document_type = kwargs.get("document_type")
    document_name = kwargs.get("document_name")
    from_user = kwargs.get("from_user", frappe.session.user)
    
    created_logs = []
    
    for recipient in recipients:
        try:
            # ✅ Check if user exists
            if not frappe.db.exists("User", recipient):
                frappe.log_error(
                    f"Skipped creating notification. User {recipient} does not exist.",
                    "Notification Log Creation"
                )
                continue
            
            # Create notification log document
            notification_doc = frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "type": notification_type,
                "document_type": document_type,
                "document_name": document_name,
                "for_user": recipient,
                "from_user": from_user,
                "email_content": message
            })
            
            # Insert the document
            notification_doc.insert(ignore_permissions=True)
            created_logs.append(notification_doc)
        
        except Exception as e:
            frappe.log_error(
                f"Failed to create notification for user {recipient}: {str(e)}",
                "Notification Log Creation"
            )
            continue
    
    return created_logs



# Example usage functions:

def create_simple_notification(user, subject, message):
    """Simple wrapper for basic notifications"""
    return create_notification_log(
        recipients=user,
        subject=subject,
        message=message
    )

def create_document_notification(recipients, subject, message, doc_type, doc_name):
    """Create notification linked to a specific document"""
    return create_notification_log(
        recipients=recipients,
        subject=subject,
        message=message,
        document_type=doc_type,
        document_name=doc_name,
        type="Alert"
    )

def create_bulk_notification(user_list, subject, message):
    """Create notifications for multiple users at once"""
    return create_notification_log(
        recipients=user_list,
        subject=subject,
        message=message
    )