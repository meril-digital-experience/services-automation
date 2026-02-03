"""
Approval Policy Matching and Stage Navigation Module.

This module handles the core logic for:
1. Policy matching - Finding the best-fit approval policy for a document based on conditions
2. Stage navigation - Determining current, next, and subsequent approval stages
3. Approver resolution - Finding the appropriate approver for each stage

Key Concepts:

Approval Policy:
    A configuration that defines which documents need approval and the sequence
    of approval stages. Policies can have conditions (filters) that determine
    which documents they apply to.

Approval Stage:
    A step in the approval workflow. Each stage defines who should approve
    (by role or specific user) and whether the stage is optional.

Stage Index (idx):
    Frappe uses 1-based indexing for child table rows. Stage 1 is the first
    approval stage, Stage 2 is the second, etc.

    Stage navigation uses idx offsets:
    - `idx - 1`: Creates a "stub" stage before stage 1 (used for initialization)
    - `idx + 1`: Gets the next stage in sequence
    - `idx + 2`: Gets two stages ahead (for look-ahead logic)

Policy Matching Algorithm:
    1. Load all enabled policies for the doctype
    2. Evaluate ALL conditions for each policy against the document
    3. A policy matches only if ALL its conditions are True
    4. Select the policy with the most matching conditions (most specific wins)
    5. On ties, prefer the most recently created policy
    6. If no match, fall back to a policy with no conditions (if exists)

State Flow:
    Document Created
         |
         v
    [Policy Matched] --> Create Approval Entry (status: Pending)
         |
         v
    [Stage 1] --> [Stage 2] --> ... --> [Final Stage] --> Approved
         |             |                      |
         +-------------+----------------------+--> Rejected
"""

import fnmatch

import frappe

from servicesapp.overwrite.approval.utils.approval.user import get_user_for_approval


def get_approval_policy(doctype: str, user_type: str) -> dict:
	return {
		"doctype": doctype,
		"user_type": user_type,
	}  # Implementation of approval policy retrieval goes here


def has_active_policy_for_doctype(doctype: str) -> bool:
	"""Return True if there is at least one enabled policy configured for the doctype."""
	if not doctype:
		return False

	return bool(
		frappe.db.exists(
			"Approval Policy",
			{
				"applies_to_doctype": doctype,
				"enabled": 1,
			},
		)
	)

	# Helpers for safe, consistent comparisons


def _safe_str(value):
	return "" if value is None else str(value)


def _split_csv(value):
	if value is None:
		return []
	# ensure string, split and strip per-item; drop empty entries
	return [s.strip() for s in str(value).split(",") if s.strip()]


def _like_match(actual, expected):
	"""Case-insensitive SQL LIKE using glob semantics via fnmatch.
	- Returns False if expected is empty/None.
	- Auto-wraps expected with % if it has no % at either end.
	"""
	if expected is None:
		return False
	actual_str = _safe_str(actual)
	expected_str = _safe_str(expected)
	if expected_str == "":
		return False

	has_leading_pct = expected_str.startswith("%")
	has_trailing_pct = expected_str.endswith("%")
	if not has_leading_pct and not has_trailing_pct:
		pattern_sql = f"%{expected_str}%"
	else:
		pattern_sql = expected_str

	# glob pattern; apply casefold to emulate typical CI collations
	pattern_glob = pattern_sql.replace("%", "*").replace("_", "?")
	return fnmatch.fnmatchcase(actual_str.casefold(), pattern_glob.casefold())


def get_approval_policy_multiple_condition(doctype, docname):
	"""
	Returns the Approval Policy whose ALL conditions match,
	falling back to the latest “no-condition” policy if none match.
	If multiple match, returns the one with the highest match_count,
	and—on ties—the most recently created.
	"""

	allow_creation_on_policy_match = frappe.db.get_single_value(
		"Approval Policy Settings", "allow_creation_on_policy_match"
	)

	# 1) Load candidates names in creation order
	# filters = {"applies_to_doctype": doctype, "enabled": 1}
	or_filters = []
	filters = [
		["Approval Policy", "applies_to_doctype", "=", doctype],
		["Approval Policy", "enabled", "=", 1],
	]

	names = frappe.get_all(
		"Approval Policy",
		filters=filters,
		or_filters=or_filters,
		fields=["name"],
	)
	if not names and not allow_creation_on_policy_match:
		frappe.throw(frappe._("No active Approval Policy found."), frappe.DoesNotExistError)

	# 2) Load the target doc
	doc = frappe.get_doc(doctype, docname)

	scored_matches = []  # list of (policy_doc, match_count)
	fallbacks = []

	# 3) Evaluate each policy's child-table of conditions
	import json

	for row in names:
		m = frappe.get_doc("Approval Policy", row.name).as_dict()
		# count how many conditions were satisfied
		match_count = 0
		ok = True

		filters_json = m.get("filters_json")
		if filters_json and filters_json != "[]":
			try:
				filters = json.loads(filters_json)
				for f in filters:
					# f is [doctype, field, op, value]
					if len(f) < 4:
						continue
					fieldname = f[1]
					op = f[2]
					value = f[3]

					actual = doc.get(fieldname)
					if not _compare(actual, op, value):
						ok = False
						break
					match_count += 1
			except Exception:
				ok = False
		else:
			# any child-table conditions?
			for cond in getattr(m, "conditions", []):
				if not ok:
					break

				actual = doc.get(cond.conditional_field)
				expected = cond.value
				op = cond.condition  # e.g. 'Equals', 'Not Equals', 'Like', etc.

				# Map legacy operators to standard ones for _compare
				op_map = {
					"Equals": "=",
					"Not Equals": "!=",
					"Like": "like",
					"Not Like": "not like",
					"In": "in",
					"Not In": "not in",
				}
				std_op = op_map.get(op, "=")

				if not _compare(actual, std_op, expected):
					ok = False
				else:
					match_count += 1

		# classify
		if not m.conditional_field and not getattr(m, "conditions", None) and not filters_json:
			# no conditions at all → fallback candidate
			fallbacks.append(m)
		elif ok and match_count > 0:
			scored_matches.append((m, match_count))

	policy_doc = None

	# 4) Pick the winner by highest match_count, breaking ties by creation order
	if scored_matches:
		# since names were loaded in creation-desc order, ties preserve that order
		scored_matches.sort(key=lambda x: x[1], reverse=True)
		policy_doc = scored_matches[0][0]
	elif fallbacks:
		policy_doc = fallbacks[0]
	else:
		if not allow_creation_on_policy_match:
			frappe.db.rollback()
			frappe.throw(
				frappe._("No active Approval Policy matched your conditions."),
				frappe.DoesNotExistError,
			)

	return policy_doc


def _compare(actual, op, expected):
	# Handle None
	if actual is None:
		actual = ""
	if expected is None:
		expected = ""

	actual_str = str(actual)
	expected_str = str(expected)

	# Try to convert to float for numeric comparisons
	try:
		actual_f = float(actual)
		expected_f = float(expected)
		is_numeric = True
	except (ValueError, TypeError):
		is_numeric = False
		actual_f = expected_f = 0

	if op == "=":
		return actual_str == expected_str
	elif op == "!=":
		return actual_str != expected_str
	elif op == "like":
		return _like_match(actual, expected)
	elif op == "not like":
		return not _like_match(actual, expected)
	elif op == "in":
		items = [s.strip() for s in expected_str.split(",") if s.strip()]
		return actual_str in items
	elif op == "not in":
		items = [s.strip() for s in expected_str.split(",") if s.strip()]
		return actual_str not in items
	elif op == ">":
		return actual_f > expected_f if is_numeric else actual_str > expected_str
	elif op == "<":
		return actual_f < expected_f if is_numeric else actual_str < expected_str
	elif op == ">=":
		return actual_f >= expected_f if is_numeric else actual_str >= expected_str
	elif op == "<=":
		return actual_f <= expected_f if is_numeric else actual_str <= expected_str

	return False


def _get_last_approval_entry(approval_entry_doc):
	entries = approval_entry_doc.get("approval_entry", []) or []
	if not entries:
		return None

	return entries[-1]


def _load_approvals(approval_policy):
	policy_doc = frappe.get_doc("Approval Policy", approval_policy)
	return policy_doc.get("approvals", []) or []


def _find_stage_by_idx(approvals, index):
	target_idx = int(index)
	for stage in approvals:
		if int(stage.get("idx")) == target_idx:
			return stage

	return None


def _get_stage_by_field(
	approval_entry_doc=None,
	field_name: str | None = None,
	stage_idx: int | None = None,
	stage_offset: int = 0,
	approval_policy: str | None = None,
) -> dict | None:
	policy_name = approval_policy

	if not policy_name and approval_entry_doc:
		policy_name = approval_entry_doc.get("approval_policy")

	if not policy_name:
		return None

	approvals = _load_approvals(policy_name)

	if stage_idx is None:
		if not (field_name and approval_entry_doc):
			return None

		last_entry = _get_last_approval_entry(approval_entry_doc)
		if not last_entry:
			return None

		raw_index = last_entry.get(field_name)
		if raw_index is None:
			return None

		stage_idx = int(raw_index) + 1

	return _find_stage_by_idx(approvals, stage_idx + stage_offset)


def get_current_stage(approval_entry_doc=None, approval_policy: str | None = None) -> dict | None:
	if approval_entry_doc:
		return _get_stage_by_field(
			approval_entry_doc=approval_entry_doc,
			field_name="current_stage",
			approval_policy=approval_policy,
		)

	if approval_policy:
		return _get_stage_by_field(
			stage_idx=0,
			stage_offset=1,
			approval_policy=approval_policy,
		)

	return None


def get_next_stage(
	approval_entry_doc=None, current_stage=None, approval_policy: str | None = None
) -> dict | None:
	if current_stage:
		return _get_stage_by_field(
			approval_entry_doc=approval_entry_doc,
			stage_idx=current_stage.get("idx"),
			stage_offset=1,
			approval_policy=approval_policy,
		)
	return _get_stage_by_field(
		approval_entry_doc=approval_entry_doc,
		field_name="current_stage",
		stage_offset=1,
		approval_policy=approval_policy,
	)


def get_next_to_next_stage(
	approval_entry_doc=None,
	current_stage=None,
	approval_policy: str | None = None,
) -> dict | None:
	if current_stage:
		return _get_stage_by_field(
			approval_entry_doc=approval_entry_doc,
			stage_idx=current_stage.get("idx"),
			stage_offset=2,
			approval_policy=approval_policy,
		)
	return _get_stage_by_field(
		approval_entry_doc=approval_entry_doc,
		field_name="current_stage",
		stage_offset=2,
		approval_policy=approval_policy,
	)


def _get_next_approval_user(
	current_stage,
	approval_entry_doc=None,
	user_type=None,
	user_id=None,
	required_optional=False,
	approval_policy: str | None = None,
):
	policy_name = approval_policy or (
		approval_entry_doc.get("approval_policy") if approval_entry_doc else None
	)

	next_stage = get_next_stage(
		approval_entry_doc=approval_entry_doc,
		current_stage=current_stage,
		approval_policy=policy_name,
	)

	if not next_stage:
		return None, None

	if next_stage.get("is_optional") and not required_optional:
		return _get_next_approval_user(
			next_stage,
			approval_entry_doc=approval_entry_doc,
			user_type=user_type,
			user_id=user_id,
			required_optional=required_optional,
			approval_policy=policy_name,
		)

	approver_type = next_stage.get("approver_type")

	if approver_type == "User":
		if not next_stage.get("employee"):
			frappe.throw("No employee configured in Approval Policy for the next stage.")
		return next_stage.get("employee"), next_stage

	next_approval_role = next_stage.get("role")
	next_approver = None

	if user_type == "employee":
		next_approver = get_user_for_approval(user_id, next_approval_role, check_cur_user=True)

	if not next_approver:
		return _get_next_approval_user(
			next_stage,
			approval_entry_doc=approval_entry_doc,
			user_type=user_type,
			user_id=user_id,
			required_optional=required_optional,
			approval_policy=policy_name,
		)

	return next_approver, next_stage
