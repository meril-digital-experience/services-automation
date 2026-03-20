// Copyright (c) 2026, Meril and contributors
// For license information, please see license.txt

frappe.ui.form.on("Account Master", {
    onload: function(frm) {
        if (frappe.session.user !== "Administrator") {
            frm.set_df_property("company", "hidden", 1);
        }
    },

    meril_division: function(frm) {
        if (!frm.doc.meril_division) return;

        frappe.db.get_value("Company", 
            { company_name: frm.doc.meril_division }, 
            "name"
        ).then(r => {
            if (r.message && r.message.name) {
                frm.set_value("company", r.message.name);
            } else {
                frappe.msgprint("No Company found for this Meril Division");
                frm.set_value("company", null);
            }
        });
    }
});
