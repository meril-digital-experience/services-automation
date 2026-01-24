frappe.ui.form.on('Instrument Application Master', {
	onload : function(frm){
	    if(frm.is_new){
	        frm.set_value('instrument_application_owner', frappe.session.user_fullname);
	    }
	    
	}
})