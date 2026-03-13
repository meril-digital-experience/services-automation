frappe.ui.form.on('Contract Master', {
    onload(frm) {
        if (frm.is_new()) {
            frm.set_value('contract_master_owner', frappe.session.user_fullname);
        }
    },

    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Generate PM Calls'), () => {
                frm.call({
                    method: "generate_pm_calls",
                    doc: frm.doc,
                    freeze: true,
                    freeze_message: __("Generating PM Calls..."),
                    callback(r) {
                        if (r.message !== undefined) {
                            frappe.show_alert({
                                message: __('PM Calls generated successfully'),
                                indicator: 'green'
                            });
                        }
                    }
                });
            });
        }
    },

    pm_frequency_period(frm) {
        if (!frm.doc.pm_frequency_period) return;

        frm.call({
            method: "calculate_pm_dates",
            doc: frm.doc,
            freeze: true,
            freeze_message: __("Calculating PM Dates..."),
            callback(r) {
                if (r.message) {
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __('PM Dates Generated successfully'),
                        indicator: 'green'
                    });
                }
            }
        });
    }


});
