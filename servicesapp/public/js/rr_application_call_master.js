frappe.ui.form.on('RR Application Call Master', {
	onload : function(frm){
	    if(frm.is_new){
	        frm.set_value('rr_application_call_owner', frappe.session.user_fullname);
	    }
	    
	}
})