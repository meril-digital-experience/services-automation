frappe.ui.form.on('Asset Master', {
    onload(frm) {
        if (frm.is_new()) {
            frm.set_value('asset_owner', frappe.session.user_fullname);
        }
    },

    // product_name(frm) {
    //     // Serial number generation moved to server-side (before_save) for data integrity
    // },

    asset_name(frm) {
        if (!frm.doc.product_name) return;

        frappe.call({
            method: "servicesapp.servicesapp.doctype.asset_master.asset_master.get_asset_name",
            args: {
                product_name: frm.doc.product_name
            },
            callback(r) {
                if (r.message) {
                    frm.set_value("asset_name", r.message);
                }
            }
        });
    }

    // before_save(frm) {
    //     if (!frm.doc.asset_name || frm.doc.asset_name.includes("new-asset-master")) {
    //         let asset_random = Math.floor(10000 + Math.random() * 90000);
    //         frm.set_value('asset_name', "MDPL00" + asset_random);
    //     }
    // }
});

