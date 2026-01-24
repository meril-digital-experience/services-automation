frappe.ui.form.on('PM Frequency Master', {
	onload: function(frm){
	    if(frm.is_new){
	        frm.set_value('preventive_maintenance_owner', frappe.session.user_fullname);
	    }
	}
})