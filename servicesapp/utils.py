import frappe
import random

def assign_engineer(doc):
    target_date = doc.call_schedule_date
    asset_id = doc.asset_no 
    
    if not target_date or not asset_id:
        frappe.throw("Call Schedule Date and Asset No are required.")

    product_id = frappe.db.get_value("Asset Master", asset_id, "product_name")

    if not product_id:
        frappe.throw(f"Asset {asset_id} is not linked to any Product in the Asset Master.")

    company_code = frappe.db.get_value("Product Master", product_id, "client_name")

    if not company_code:
        frappe.throw(f"The Product {product_id} has no Client Name (Company Code) assigned.")

    
    engineers = frappe.get_all("Employee", 
        filters={
            "role": "Service Engineer", 
            "status": "Active",
            "company": company_code
        },
        fields=["name"]
    )

    if not engineers:
        frappe.throw(f"No active engineers found for company code: {company_code}")

    
    engineer_stats = []
    for emp in engineers:
        total = frappe.db.count(doc.doctype, {"assigned_engineer": emp.name})
        daily = frappe.db.count(doc.doctype, {
            "assigned_engineer": emp.name, 
            "call_schedule_date": target_date
        })
        engineer_stats.append({"name": emp.name, "total": total, "daily": daily})

    # Sort
    engineer_stats.sort(key=lambda x: (x['total'], x['daily']))
    selected = random.choice([e['name'] for e in engineer_stats if e['total'] == engineer_stats[0]['total']])
    
    
    doc.assigned_engineer = selected
    update_employee_table(selected, target_date, doc)

def update_employee_table(employee_id, date, source_doc):
    emp_doc = frappe.get_doc("Employee", employee_id)
    emp_doc.append("assigned_calls", {
        "date": date,
        "total_calls": 1,
        "doctype_name": source_doc.doctype,
        "doctype_id": source_doc.name       
    })
    emp_doc.total_calls = len(emp_doc.assigned_calls)
    emp_doc.save(ignore_permissions=True)