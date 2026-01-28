frappe.ui.form.on('Distributor Master', {
	onload: function(frm){
	    if(frm.is_new){
	        frm.set_value('distributor_owner', frappe.session.user_fullname);
	    }
	}
})