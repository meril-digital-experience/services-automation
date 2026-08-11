import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def setup():
    frappe.flags.in_install = True
    
    # Create Child Table Doctype
    if not frappe.db.exists("DocType", "Employee Product Skill"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Employee Product Skill",
            "module": "Servicesapp",
            "custom": 0,
            "istable": 1,
            "fields": [
                {
                    "fieldname": "product",
                    "fieldtype": "Link",
                    "label": "Product",
                    "options": "Product Master",
                    "in_list_view": 1,
                    "reqd": 1
                }
            ]
        })
        doc.insert(ignore_permissions=True)
        print("Created Employee Product Skill DocType")
    else:
        print("Employee Product Skill DocType already exists")
        
    # Add Custom Field to Employee
    create_custom_field("Employee", {
        "fieldname": "product_skills",
        "label": "Product Skills",
        "fieldtype": "Table",
        "options": "Employee Product Skill",
        "insert_after": "department"
    })
    print("Added product_skills Custom Field to Employee")
    
    frappe.db.commit()
