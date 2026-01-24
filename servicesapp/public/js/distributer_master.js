frappe.ui.form.on('Distributer Master', {
	onload: function(frm){
	    if(frm.is_new){
	        frm.set_value('distributer_owner', frappe.session.user_fullname);
	    }
	}
})