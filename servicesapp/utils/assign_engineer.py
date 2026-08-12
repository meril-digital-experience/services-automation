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


def get_assignment_from_rules(doc, city, company, product):
    """
    Scaffold for checking dynamic Assignment Rules DocType.
    This will query rules where City, Company, and Product match.
    """
    if frappe.db.exists("DocType", "Engineer Assignment Rule"):
        filters = {
            "city": city,
            "company": company,
            "product": product
        }
        
        # Try finding a rule that matches all three
        assigned_to = frappe.db.get_value("Engineer Assignment Rule", filters, "assigned_engineer")
        if assigned_to:
            return assigned_to
            
        # Try finding a rule that matches just city and company (product is agnostic)
        filters.pop("product", None)
        filters["product"] = ["is", "not set"]
        assigned_to = frappe.db.get_value("Engineer Assignment Rule", filters, "assigned_engineer")
        if assigned_to:
            return assigned_to
            
    return None

def assign_engineer(doc):

    target_date = doc.call_schedule_date

    # Get product, city, company dynamically
    product_id, city, company_code = get_product_and_city(doc)

    if not company_code:
        if product_id:
            msg = f"Product {product_id} has no Client Name (Company Code). Engineer could not be assigned."
        elif doc.doctype == "RR Application Call Master":
            msg = f"Account '{doc.account_name}' has no Company assigned. Engineer could not be assigned."
        else:
            msg = "No Company Code found. Engineer could not be assigned."
            
        frappe.msgprint(
            msg=msg,
            title="Assignment Pending",
            indicator="orange"
        )
        return

    if not city:
        frappe.msgprint(
            msg="City not found for assignment. Engineer could not be assigned.",
            title="Assignment Pending",
            indicator="orange"
        )
        return

    # DYNAMIC ASSIGNMENT RULE CHECK (ZOHO STYLE)
    rule_assigned_engineer = get_assignment_from_rules(doc, city, company_code, product_id)
    if rule_assigned_engineer:
        doc.assigned_engineer = rule_assigned_engineer
        print(f"Assigned Engineer (via Rule): {rule_assigned_engineer}")
        send_assignment_email(doc, rule_assigned_engineer)
        update_employee_table(rule_assigned_engineer, doc)
        return

    # FETCH ENGINEERS (FALLBACK / LOAD BALANCING)
    all_engineers = frappe.db.sql("""
        SELECT DISTINCT e.name 
        FROM `tabEmployee` e
        LEFT JOIN `tabMultiple Company Name` mc ON mc.parent = e.name
        LEFT JOIN `tabMultiple City` ml ON ml.parent = e.name
        WHERE e.role = 'Service Engineer' 
          AND e.status = 'Active'
          AND (e.company = %(company)s OR mc.company_name = %(company)s)
          AND (e.location = %(city)s OR ml.location = %(city)s)
    """, {
        "company": company_code,
        "city": city
    }, as_dict=True)

    if not all_engineers:
        frappe.msgprint(
            msg=f"No active engineers found for {company_code} in {city}. The document has been saved, but you must manually select an Engineer in the 'Assigned Engineer' field on this form.",
            title="Assignment Pending",
            indicator="orange"
        )
        return

    # TIER 2: SKILL-BASED FILTERING
    skilled_engineers = []
    if product_id:
        # Check which engineers have this product skill
        emp_names = [e.name for e in all_engineers]
        if frappe.db.exists("DocType", "Employee Product Skill"):
            skilled_records = frappe.get_all(
                "Employee Product Skill", 
                filters={"parent": ["in", emp_names], "product": product_id},
                fields=["parent"]
            )
            skilled_names = list(set([r.parent for r in skilled_records]))
            skilled_engineers = [e for e in all_engineers if e.name in skilled_names]

    # If we have skilled engineers, use them. Otherwise, fall back to all engineers in the city (Tier 3)
    final_engineers = skilled_engineers if skilled_engineers else all_engineers

    # LOAD BALANCING LOGIC (OPTIMIZED)
    engineer_names = tuple([emp.name for emp in final_engineers])
    
    total_counts = frappe.db.sql(f"""
        SELECT assigned_engineer, COUNT(*) as count 
        FROM `tab{doc.doctype}` 
        WHERE assigned_engineer IN %s 
        GROUP BY assigned_engineer
    """, (engineer_names,), as_dict=True)
    total_map = {row.assigned_engineer: row.count for row in total_counts}

    daily_counts = frappe.db.sql(f"""
        SELECT assigned_engineer, COUNT(*) as count 
        FROM `tab{doc.doctype}` 
        WHERE assigned_engineer IN %s AND call_schedule_date = %s
        GROUP BY assigned_engineer
    """, (engineer_names, target_date), as_dict=True)
    daily_map = {row.assigned_engineer: row.count for row in daily_counts}

    engineer_stats = []
    for emp_name in engineer_names:
        engineer_stats.append({
            "name": emp_name,
            "total": total_map.get(emp_name, 0),
            "daily": daily_map.get(emp_name, 0)
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

        company = account.company if account else None
        return None, doc.select_billing_city, company

    # OTHER CALL
    if doc.doctype == "Other Calls Issue Master":

        if doc.other_calls_regarding == "Asset":

            asset_info = frappe.db.get_value(
                "Asset Master",
                doc.asset_no,
                ["product_name", "account_city"],
                as_dict=True
            )

            if not asset_info:
                product_name = getattr(doc, "product_name", None)
                city = getattr(doc, "city_name", None) or getattr(doc, "account_city", None) or getattr(doc, "city", None)
                if not product_name:
                    frappe.throw(f"Asset {doc.asset_no} not found in Asset Master.")
            else:
                product_name = asset_info.product_name
                city = asset_info.account_city

            company_code = frappe.db.get_value(
                "Product Master",
                product_name,
                "client_name"
            ) if product_name else None

            return product_name, city, company_code

        elif doc.other_calls_regarding == "Account":

            account = frappe.db.get_value(
                "Account Master",
                doc.account_name,
                ["company"],
                as_dict=True
            )

            return None, doc.city_name, account.company if account else None

    # DEFAULT (ALL OTHER DOCTYPES)
    asset_info = frappe.db.get_value(
        "Asset Master",
        doc.asset_no,
        ["product_name", "account_city"],
        as_dict=True
    )

    if not asset_info:
        product_name = getattr(doc, "product_name", None)
        city = getattr(doc, "city_name", None) or getattr(doc, "account_city", None) or getattr(doc, "city", None)
        if not product_name:
            frappe.throw(f"Asset {doc.asset_no} not found in Asset Master.")
    else:
        product_name = asset_info.product_name
        city = asset_info.account_city

    company_code = frappe.db.get_value(
        "Product Master",
        product_name,
        "client_name"
    ) if product_name else None

    return product_name, city, company_code


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