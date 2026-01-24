frappe.ui.form.on('Asset Master', {
	onload : function(frm){
	    if(frm.is_new){
	        frm.set_value('asset_owner', frappe.session.user_fullname);
	    }
	    
	}
})