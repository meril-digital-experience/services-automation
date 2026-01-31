frappe.ui.form.on('Asset Master', {
    onload: function(frm) {
        if (frm.is_new) {
            frm.set_value('asset_owner', frappe.session.user_fullname);
        }
    },

    product_name: function(frm) {
        if (frm.doc.product_name) {
            
            frappe.db.get_value('Product Master', frm.doc.product_name, 'product_short_code', (r) => {
                if (r && r.product_short_code) {
                    
                    let short_code = r.product_short_code.replace('-', ''); 
                    
                   
                    let random_part = Math.floor(100000 + Math.random() * 900000).toString();
                    
                    
                    let combined = short_code + random_part;
                    let final_serial = combined.substring(0, 9);
                    
                    
                    frm.set_value('serial_no', final_serial);
                }
            });
        }
    },

    before_save: function(frm) {
        if (!frm.doc.asset_name || frm.doc.asset_name.includes("new-asset-master")) {
            let asset_random = Math.floor(10000 + Math.random() * 90000);
            frm.set_value('asset_name', "MDPL00" + asset_random);
        }
    }
});