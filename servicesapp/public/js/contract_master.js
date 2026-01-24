frappe.ui.form.on('Contract Master', {
	onload: function(frm){
	    if(frm.is_new){
	        frm.set_value('contract_master_owner', frappe.session.user_fullname);
	    }
	}
})