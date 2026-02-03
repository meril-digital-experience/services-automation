frappe.ui.form.on('Product Master', {
    onload(frm) {
        if (frm.is_new()) {
            frm.set_value('product_owner', frappe.session.user_fullname);
        }
    },

    before_save(frm) {
        if (!frm.doc.client_code) {
            frm.set_value('client_name', null);
            return;
        }

        return frappe.db.get_value(
            'Company',
            { sap_client_code: frm.doc.client_code },
            'name'
        ).then(r => {
            if (r && r.message && r.message.name) {
                frm.set_value('client_name', r.message.name);
            } else {
                frappe.throw(
                    __('No Company found for Client Code: {0}', [frm.doc.client_code])
                );
            }
        });
    }
});
