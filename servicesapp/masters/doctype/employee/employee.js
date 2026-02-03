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
