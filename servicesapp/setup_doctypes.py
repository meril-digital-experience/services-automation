import frappe

def create_doctypes():
    frappe.flags.in_install = True
    
    # 1. Create SLA Settings DocType
    if not frappe.db.exists("DocType", "SLA Settings"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "SLA Settings",
            "module": "Servicesapp",
            "custom": 0,
            "issingle": 1,
            "fields": [
                {
                    "fieldname": "initial_escalation_hours",
                    "fieldtype": "Int",
                    "label": "Initial Escalation Hours",
                    "default": "24"
                },
                {
                    "fieldname": "higher_level_escalation_hours",
                    "fieldtype": "Int",
                    "label": "Higher Level Escalation Hours",
                    "default": "24"
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1
                }
            ]
        })
        doc.insert(ignore_permissions=True)
        print("Created SLA Settings DocType")
    else:
        print("SLA Settings already exists")

    # 2. Create Assignment Rule DocType
    if not frappe.db.exists("DocType", "Assignment Rule"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Assignment Rule",
            "module": "Servicesapp",
            "custom": 0,
            "fields": [
                {
                    "fieldname": "city",
                    "fieldtype": "Link",
                    "label": "City",
                    "options": "City Master"
                },
                {
                    "fieldname": "company",
                    "fieldtype": "Link",
                    "label": "Company",
                    "options": "Company"
                },
                {
                    "fieldname": "product",
                    "fieldtype": "Link",
                    "label": "Product",
                    "options": "Product Master"
                },
                {
                    "fieldname": "assigned_engineer",
                    "fieldtype": "Link",
                    "label": "Assigned Engineer",
                    "options": "Employee"
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1
                }
            ],
            "autoname": "AR-.####"
        })
        doc.insert(ignore_permissions=True)
        print("Created Assignment Rule DocType")
    else:
        print("Assignment Rule already exists")
    
    frappe.db.commit()
