<h3>Missed Call Escalation</h3>

<p>An instrument service call (<b>{{ doc.record }}</b>) was not closed by the scheduled date.</p>

<p><b>Approver:</b> {{ doc.approval_entry[0].approver_user }}</p>

<p><b>System Remark:</b> {{ doc.approval_entry[0].remarks }}</p>

<hr>

<p>Please click below to review and take action:</p>

<p><a href="{{ frappe.utils.get_url_to_form('Approval Entry', doc.name) }}">View Approval Entry</a></p>
