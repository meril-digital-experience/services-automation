frappe.ui.form.on('Contract Master', {
    // Event 1
    onload: function(frm) {
        if (frm.is_new()) {
            frm.set_value('contract_master_owner', frappe.session.user_fullname);
        }
    },

    // Event 2
    refresh: function(frm) {
        frm.add_custom_button(__('Generate PM Dates'), function() {
            frm.call({
                method: "calculate_pm_dates",
                doc: frm.doc,
                callback: function(r) {
                    if (r.message) {
                        frm.reload_doc(); 
                        frappe.show_alert({
                            message: __('PM Dates Generated successfully'),
                            status: 'green'
                        });
                    }
                }
            });
        }, __("Actions"));
    }
});