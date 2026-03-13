frappe.ui.form.on('Account Master', {
    onload: function(frm) {
        if(frm.is_new){
            frm.set_value('account_owner', frappe.session.user_fullname);
        }
    }
})

// frappe.ui.form.on('Account Master', {
//     onload(frm) {
//         if (!frm.is_new()) return;

//         frappe.db.get_value(
//             'Employee',
//             { company_email: frappe.session.user },
//             'name'
//         ).then(r => {
//             if (r && r.message && r.message.name) {
//                 frm.set_value('account_owner', r.message.name);
//             }
//         });
//     }
// });
