frappe.ui.form.on('Instrument Breakdown Master', {
	onload : function(frm){
	    if(frm.is_new){
	        frm.set_value('instrument_breakdown_owner', frappe.session.user_fullname);
	    }
	    
	}
})