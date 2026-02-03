frappe.ui.form.on('Asset Master', {
    onload(frm) {
        if (frm.is_new()) {
            frm.set_value('asset_owner', frappe.session.user_fullname);
        }
    },

    product_name(frm) {
        if (!frm.doc.product_name) return;

        frappe.db.get_value('Product Master', frm.doc.product_name, 'product_short_code', (r) => {
                if (!r || !r.product_short_code) return;

                let short_code = r.product_short_code.replace(/[^A-Za-z0-9]/g, '');

                short_code = short_code.substring(0, 3).toUpperCase();

                let remaining_length = 9 - short_code.length;

                let random_part = Math.random()
                    .toString()
                    .slice(2, 2 + remaining_length);

                let final_serial = short_code + random_part;

                frm.set_value('serial_no', final_serial);
            }
        );
    },

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

