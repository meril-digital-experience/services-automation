import frappe
from frappe import _
from frappe.desk.reportview import validate_args as validate_list_args
from frappe.model.db_query import DatabaseQuery
from frappe.utils import cint, sbool

from servicesapp.overwrite.approval.utils.approval.entry import get_document


ALLOWED_EXECUTE_KEYS = {
	"fields",
	"filters",
	"or_filters",
	"docstatus",
	"group_by",
	"order_by",
	"limit_start",
	"limit_page_length",
	"as_list",
	"with_childnames",
	"debug",
	"ignore_permissions",
	"user",
	"with_comment_count",
	"join",
	"distinct",
	"start",
	"page_length",
	"limit",
	"ignore_ifnull",
	"save_user_settings",
	"save_user_settings_fields",
	"update",
	"add_total_row",
	"user_settings",
	"reference_doctype",
	"run",
	"strict",
	"pluck",
	"ignore_ddl",
	"parent_doctype",
}


def _normalise_args(raw_args: dict) -> frappe._dict:
	args = frappe._dict(raw_args)

	if not args.get("doctype"):
		frappe.throw(_("doctype is required"), frappe.MandatoryError)

	args.setdefault("fields", ["*"])

	# map alternative pagination parameters to DatabaseQuery API
	if args.get("parent") and not args.get("parent_doctype"):
		args["parent_doctype"] = args.pop("parent")

	if args.get("offset") is not None and args.get("limit_start") is None:
		args["limit_start"] = args.offset
	if args.get("start") is not None and args.get("limit_start") is None:
		args["limit_start"] = args.start
	if args.get("page_length") is not None and args.get("limit_page_length") is None:
		args["limit_page_length"] = args.page_length
	if args.get("limit") is not None and args.get("limit_page_length") is None:
		args["limit_page_length"] = args.limit

	args.pop("offset", None)
	args.pop("start", None)
	args.pop("page_length", None)

	if args.get("limit_start") is not None:
		args.limit_start = cint(args.limit_start)
	if args.get("limit_page_length") is not None:
		args.limit_page_length = cint(args.limit_page_length)
	if args.get("limit") is not None:
		args.limit = cint(args.limit)

	bool_keys = (
		"with_childnames",
		"debug",
		"ignore_permissions",
		"with_comment_count",
		"distinct",
		"ignore_ifnull",
		"save_user_settings",
		"strict",
		"run",
	)
	for key in bool_keys:
		if key in args and args[key] is not None:
			args[key] = sbool(args[key])

	if "as_list" in args:
		args.as_list = sbool(args.as_list)
	else:
		as_dict_flag = args.pop("as_dict", True)
		args.as_list = not sbool(as_dict_flag)

	validate_list_args(args)

	return args


def _build_query_kwargs(args: frappe._dict) -> dict:
	return {key: value for key, value in args.items() if key in ALLOWED_EXECUTE_KEYS and value is not None}


def _get_total_count(doctype: str, base_kwargs: dict) -> int:
	count_kwargs = frappe._dict(base_kwargs)

	for key in ("limit_start", "limit_page_length", "start", "page_length", "limit"):
		count_kwargs.pop(key, None)

	# remove options that add metadata to the result but aren't required for counts
	for key in (
		"pluck",
		"with_childnames",
		"with_comment_count",
		"add_total_row",
		"save_user_settings",
		"save_user_settings_fields",
		"user_settings",
	):
		count_kwargs.pop(key, None)

	count_kwargs["order_by"] = None
	count_kwargs["run"] = False
	count_kwargs["as_list"] = False

	# reuse the same query (minus pagination) and wrap it to count the resulting rows
	count_query = DatabaseQuery(doctype).execute(**count_kwargs).strip().rstrip(";")
	if not count_query:
		return 0

	return cint(frappe.db.sql(f"select count(*) from ({count_query}) as _total_count")[0][0])


# master_data_suite.api.approval.resource.get_list_with_count
@frappe.whitelist()
def get_list_with_count(**kwargs):
	args = _normalise_args(kwargs)
	doctype = args.doctype
	query_kwargs = _build_query_kwargs(args)

	records = DatabaseQuery(doctype).execute(**query_kwargs)
	total_count = _get_total_count(doctype, query_kwargs)
	for row in records:
		row["approval_entry"] = add_approval_entry(doctype, row)
	return {"message": "success", "data": records, "total_count": total_count}


def add_approval_entry(doctype, row):
	entry = get_document(doctype, row.name)
	return entry.get("next_approver") if entry else None
