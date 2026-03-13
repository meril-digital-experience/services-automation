// Copyright (c) 2026, Meril and contributors
// For license information, please see license.txt

frappe.ui.form.on('Instrument Breakdown Master', {
    refresh(frm) {
        if (frm.timer_interval) clearInterval(frm.timer_interval);

        if (frm.doc.workflow_state === "Escalated" && frm.doc.escalated_on) {
            render_timer(frm);
            frm.timer_interval = setInterval(() => update_timer(frm), 1000);
        } else {
            remove_timer(frm);
        }
    }
});

function render_timer(frm) {
    remove_timer(frm);

    frm.$timer = $(`
        <div class="escalation-banner alert alert-info">
            <h4 class="countdown">--:--:--</h4>
            <div class="status small text-muted"></div>
        </div>
    `).prependTo(frm.$wrapper.find('.form-layout'));

    update_timer(frm);
}

function update_timer(frm) {
    if (!frm.$timer) return;

    const start = new Date(frm.doc.escalated_on);
    const hours = frm.doc.escalation_deadline_hours || 24;
    const deadline = new Date(start.getTime() + hours * 3600000);
    const diff = deadline - new Date();

    const $countdown = frm.$timer.find('.countdown');
    const $status = frm.$timer.find('.status');

    if (diff <= 0) {
        $countdown.text("OVERDUE");
        frm.$timer.removeClass().addClass("escalation-banner alert alert-danger");
        $status.text("Escalation required immediately.");
        return;
    }

    const h = String(Math.floor(diff / 3600000)).padStart(2, "0");
    const m = String(Math.floor((diff % 3600000) / 60000)).padStart(2, "0");
    const s = String(Math.floor((diff % 60000) / 1000)).padStart(2, "0");

    $countdown.text(`${h}:${m}:${s}`);

    if (h < 2) {
        frm.$timer.removeClass().addClass("escalation-banner alert alert-danger");
    } else if (h < 6) {
        frm.$timer.removeClass().addClass("escalation-banner alert alert-warning");
    }
}

function remove_timer(frm) {
    if (frm.$timer) {
        frm.$timer.remove();
        frm.$timer = null;
    }
}