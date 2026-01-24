frappe.ui.form.on('Product Master', {
	onload : function(frm){
	    if(frm.is_new){
	        frm.set_value('product_owner', frappe.session.user_fullname);
	    }
	    
	}
})