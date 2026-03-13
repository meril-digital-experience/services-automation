frappe.ui.form.on('Other Calls Issue Master', {
	onload : function(frm){
	    if(frm.is_new){
	        frm.set_value('other_calls_owner', frappe.session.user_fullname);
	    }
	}
})