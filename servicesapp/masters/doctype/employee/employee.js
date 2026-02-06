// Copyright (c) 2026, Meril and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee", {
    salutation(frm) {
        set_employee_name(frm);
    },
    first_name(frm) {
        set_employee_name(frm);
    },
    last_name(frm) {
        set_employee_name(frm);
    },
    create_user(frm) {
        if (!frm.doc.company_email) {
            frappe.msgprint("Company Email is required");
            return;
        }

        if (frm.doc.user_id) {
            frappe.msgprint("User already created for this employee");
            return;
        }

        frappe.call({
            method: "servicesapp.masters.doctype.employee.employee.create_user_from_employee",
            args: {
                employee_name: frm.doc.name
            },
            freeze: true,
            callback(r) {
                if (r.message) {
                    frm.set_value("user_id", r.message);
                    frappe.msgprint("User created successfully");
                }
            }
        });
    }
});

function set_employee_name(frm) {
    let parts = [];

    if (frm.doc.salutation) {
        parts.push(frm.doc.salutation);
    }

    if (frm.doc.first_name) {
        parts.push(frm.doc.first_name);
    }

    if (frm.doc.last_name) {
        parts.push(frm.doc.last_name);
    }

    frm.set_value("employee_name", parts.join(" "));
}
