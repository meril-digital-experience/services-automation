import frappe
import random

def assign_engineer(doc):
    target_date = doc.call_schedule_date
    asset_id = doc.asset_no 
    
    
    # fetching both product_name and account_city from Asset Master
    asset_info = frappe.db.get_value("Asset Master", asset_id, ["product_name", "account_city"], as_dict=True)

    if not asset_info or not asset_info.product_name:
        frappe.throw(f"Asset {asset_id} is not linked to any Product in the Asset Master.")
    
    product_id = asset_info.product_name
    asset_city = asset_info.account_city 

    # Get Company Code
    company_code = frappe.db.get_value("Product Master", product_id, "client_name")

    if not company_code:
        frappe.throw(f"The Product {product_id} has no Client Name (Company Code) assigned.")

    # filters 
    engineers = frappe.get_all("Employee", 
        filters={
            "role": "Service Engineer", # role filter
            "status": "Active", # status
            "company": company_code, # company filter
            "location": asset_city # location filter
        },
        fields=["name"]
    )

    if not engineers:
        # if no local engineer is found
        frappe.throw(f"No active engineers found for {company_code} in the city of {asset_city}.")

    # assigning logic
    engineer_stats = []
    for emp in engineers:
        total = frappe.db.count(doc.doctype, {"assigned_engineer": emp.name})
        daily = frappe.db.count(doc.doctype, {
            "assigned_engineer": emp.name, 
            "call_schedule_date": target_date
        })
        engineer_stats.append({"name": emp.name, "total": total, "daily": daily})

    engineer_stats.sort(key=lambda x: (x['total'], x['daily']))
    selected = random.choice([e['name'] for e in engineer_stats if e['total'] == engineer_stats[0]['total']])
    
    doc.assigned_engineer = selected
    update_employee_table(selected, doc)

def update_employee_table(employee_id, source_doc):
    """Update employee's assignment table with correct date based on status"""
    
    # Determine which date to use based on call status
    if hasattr(source_doc, 'call_status') and source_doc.call_status == "In Progress":
        # Use in_progress_call_schedule_date for In Progress status
        date = source_doc.in_progress_call_schedule_date if hasattr(source_doc, 'in_progress_call_schedule_date') else source_doc.call_schedule_date
    else:
        # Use call_schedule_date for Pending/Assigned status
        date = source_doc.call_schedule_date
    
    emp_doc = frappe.get_doc("Employee", employee_id)
    emp_doc.append("assigned_calls", {
        "date": date,
        "total_calls": 1,
        "doctype_name": source_doc.doctype,
        "doctype_id": source_doc.name       
    })
    # call total
    emp_doc.total_calls = len(emp_doc.assigned_calls) 
    emp_doc.save(ignore_permissions=True)