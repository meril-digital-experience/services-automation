frappe.ui.form.on('Instrument Application Master', {
	onload : function(frm){
	    if(frm.is_new){
	        frm.set_value('instrument_application_owner', frappe.session.user_fullname);
	    }
	    
	},

	before_save: function(frm) {
        if (!frm.doc.call_closure_date) {
            frm.set_value('call_closure_date', frappe.datetime.get_today());
        }
    }
})