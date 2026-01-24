frappe.ui.form.on('Installation Request Master', {
	onload : function(frm){
	    if(frm.is_new){
	        frm.set_value('installation_request_owner', frappe.session.user_fullname);
	    }
	    
	}
})