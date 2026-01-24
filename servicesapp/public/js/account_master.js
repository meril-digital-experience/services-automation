frappe.ui.form.on('Account Master', {
    onload: function(frm) {
        if(frm.is_new){
            frm.set_value('account_owner', frappe.session.user_fullname);
        }
    }
})