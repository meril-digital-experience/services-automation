import frappe

def setup_and_seed():
    frappe.flags.in_install = True
    
    # 1. Create Engineer Assignment Rule DocType
    if not frappe.db.exists("DocType", "Engineer Assignment Rule"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Engineer Assignment Rule",
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
                    "options": "Employee",
                    "reqd": 1
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
            "autoname": "EAR-.####"
        })
        doc.insert(ignore_permissions=True)
        print("Created Engineer Assignment Rule DocType")
    else:
        print("Engineer Assignment Rule already exists")
    
    # 2. Add sample entries if empty
    if frappe.db.count("Engineer Assignment Rule") == 0:
        # Get some sample active engineers to assign
        engineers = frappe.get_all("Employee", filters={"status": "Active", "role": "Service Engineer"}, limit=2, fields=["name", "company", "location"])
        
        if engineers:
            for eng in engineers:
                # Fetch full doc to access child tables
                employee_doc = frappe.get_doc("Employee", eng.name)
                
                company = eng.company
                if not company and getattr(employee_doc, "multiple_companies", None):
                    company = employee_doc.multiple_companies[0].company_name
                
                location = eng.location
                if not location and getattr(employee_doc, "multiple_cities", None):
                    location = employee_doc.multiple_cities[0].location

                # Get a sample product for this company
                products = frappe.get_all("Product Master", filters={"client_name": company}, limit=1, fields=["name"]) if company else []
                product = products[0].name if products else None
                
                # Add a rule for this engineer's city, company, and (optional) product
                rule = frappe.get_doc({
                    "doctype": "Engineer Assignment Rule",
                    "city": location,
                    "company": company,
                    "product": product,
                    "assigned_engineer": eng.name
                })
                rule.insert(ignore_permissions=True)
                print(f"Added sample rule for Engineer {eng.name} (City: {location}, Company: {company})")
        else:
            print("No active Service Engineers found to create sample rules for.")
    else:
        print("Sample entries already exist.")
        
    frappe.db.commit()
