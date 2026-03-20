import frappe
import random
from servicesapp.utils.custom_send_email import custom_send_mail

# def assign_engineer(doc):
#     target_date = doc.call_schedule_date
#     asset_id = doc.asset_no 
    
    
#     # fetching both product_name and account_city from Asset Master
#     asset_info = frappe.db.get_value("Asset Master", asset_id, ["product_name", "account_city"], as_dict=True)

#     if not asset_info or not asset_info.product_name:
#         frappe.throw(f"Asset {asset_id} is not linked to any Product in the Asset Master.")
    
#     product_id = asset_info.product_name
#     asset_city = asset_info.account_city 

#     # Get Company Code
#     company_code = frappe.db.get_value("Product Master", product_id, "client_name")

#     if not company_code:
#         frappe.throw(f"The Product {product_id} has no Client Name (Company Code) assigned.")

#     # filters 
#     engineers = frappe.get_all("Employee", 
#         filters={
#             "role": "Service Engineer", # role filter
#             "status": "Active", # status
#             "company": company_code, # company filter
#             "location": asset_city # location filter
#         },
#         fields=["name"]
#     )

#     if not engineers:
#         # if no local engineer is found
#         frappe.throw(f"No active engineers found for {company_code} in the city of {asset_city}.")

#     # assigning logic
#     engineer_stats = []
#     for emp in engineers:
#         total = frappe.db.count(doc.doctype, {"assigned_engineer": emp.name})
#         daily = frappe.db.count(doc.doctype, {
#             "assigned_engineer": emp.name, 
#             "call_schedule_date": target_date
#         })
#         engineer_stats.append({"name": emp.name, "total": total, "daily": daily})

#     engineer_stats.sort(key=lambda x: (x['total'], x['daily']))
#     selected = random.choice([e['name'] for e in engineer_stats if e['total'] == engineer_stats[0]['total']])
    
#     doc.assigned_engineer = selected
#     print(f"Assigned Engineer: {selected}")
#     send_assignment_email(doc, selected)
#     update_employee_table(selected, doc)


def assign_engineer(doc):

    target_date = doc.call_schedule_date

    # Get product, city, company dynamically
    product_id, city, company_code = get_product_and_city(doc)

    if not company_code:
        frappe.throw(f"Product {product_id} has no Client Name (Company Code).")

    if not city:
        frappe.throw("City not found for assignment.")

    # FETCH ENGINEERS
    engineers = frappe.get_all(
        "Employee",
        filters={
            "role": "Service Engineer",
            "status": "Active",
            "company": company_code,
            "location": city
        },
        fields=["name"]
    )

    if not engineers:
        frappe.throw(f"No active engineers found for {company_code} in {city}.")

    # LOAD BALANCING LOGIC (YOUR ORIGINAL)
    engineer_stats = []

    for emp in engineers:
        total = frappe.db.count(doc.doctype, {
            "assigned_engineer": emp.name
        })

        daily = frappe.db.count(doc.doctype, {
            "assigned_engineer": emp.name,
            "call_schedule_date": target_date
        })

        engineer_stats.append({
            "name": emp.name,
            "total": total,
            "daily": daily
        })

    # sort by least total, then least daily
    engineer_stats.sort(key=lambda x: (x['total'], x['daily']))

    # pick randomly among lowest total
    lowest_total = engineer_stats[0]['total']
    candidates = [e['name'] for e in engineer_stats if e['total'] == lowest_total]

    selected = random.choice(candidates)

    # ASSIGN
    doc.assigned_engineer = selected
    print(f"Assigned Engineer: {selected}")

    send_assignment_email(doc, selected)
    update_employee_table(selected, doc)

def get_product_and_city(doc):

    # RR APPLICATION
    if doc.doctype == "RR Application Call Master":

        account = frappe.db.get_value(
            "Account Master",
            doc.account_name,
            ["company"],
            as_dict=True
        )

        return None, doc.select_billing_city, account.company

    # OTHER CALL
    if doc.doctype == "Other Calls Issue Master":

        if doc.other_calls_regarding == "Asset":

            asset_info = frappe.db.get_value(
                "Asset Master",
                doc.asset_no,
                ["product_name", "account_city"],
                as_dict=True
            )

            company_code = frappe.db.get_value(
                "Product Master",
                asset_info.product_name,
                "client_name"
            )

            return asset_info.product_name, asset_info.account_city, company_code

        elif doc.other_calls_regarding == "Account":

            account = frappe.db.get_value(
                "Account Master",
                doc.account_name,
                ["company"],
                as_dict=True
            )

            return None, doc.city_name, account.company

    # DEFAULT (ALL OTHER DOCTYPES)
    asset_info = frappe.db.get_value(
        "Asset Master",
        doc.asset_no,
        ["product_name", "account_city"],
        as_dict=True
    )

    company_code = frappe.db.get_value(
        "Product Master",
        asset_info.product_name,
        "client_name"
    )

    return asset_info.product_name, asset_info.account_city, company_code


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


def send_assignment_email(doc, engineer_id):

    print(f"Sending email for {doc.doctype}")

    # Special condition
    # if doc.doctype == "Other Calls Issue Master":
    #     if getattr(doc, "other_calls_regarding", None) != "Asset":
    #         print("Skipping email: Not Asset related")
    #         return

    engineer = frappe.get_doc("Employee", engineer_id)

    if not engineer.company_email:
        return

    # FIELD NORMALIZATION
    asset_no = (
        getattr(doc, "asset_no", None)
        or getattr(doc, "asset", None)
        or "N/A"
    )

    schedule_date = (
        getattr(doc, "call_schedule_date", None)
        or getattr(doc, "schedule_date", None)
        or getattr(doc, "date", None)
        or "N/A"
    )

    product_name = (
        getattr(doc, "product_name", None)
        or frappe.db.get_value("Asset Master", asset_no, "product_name")
        or "N/A"
    )

    account_name = getattr(doc, "account_name", None) or "N/A"

    # DOCTYPE LABEL MAPPING
    label_map = {
        "Installation Request Master": "Installation Request",
        "Instrument Breakdown Master": "Breakdown Request",
        "RR Application Call": "RR Call",
        "Instrument Application Master": "Application Request",
        "Other Call Master": "Other Request"
    }

    request_type = label_map.get(doc.doctype, doc.doctype)

    context = {
        "doc": doc,
        "engineer": engineer,
        "doc_link": frappe.utils.get_url_to_form(doc.doctype, doc.name),
        "asset_no": asset_no,
        "schedule_date": schedule_date,
        "request_type": request_type,
        "product_name": product_name,
        "account_name": account_name
    }

    custom_send_mail(
        mail_template="Dynamic Assignment Email",
        recipient=engineer.company_email,
        email_context=context,
        now=True
    )