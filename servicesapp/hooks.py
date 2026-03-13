app_name = "servicesapp"
app_title = "Servicesapp"
app_publisher = "Meril"
app_description = "Service Management App"
app_email = "rishi.hingad@merillife.com"
app_license = "mit"


# Scheduled Tasks
# ---------------
scheduler_events = {
    "daily": [
 		"servicesapp.tasks.check_for_missed_calls"
 	],
}


# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "servicesapp",
# 		"logo": "/assets/servicesapp/logo.png",
# 		"title": "Servicesapp",
# 		"route": "/servicesapp",
# 		"has_permission": "servicesapp.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/servicesapp/css/servicesapp.css"
# app_include_js = "/assets/servicesapp/js/servicesapp.js"

# include js, css files in header of web template
# web_include_css = "/assets/servicesapp/css/servicesapp.css"
# web_include_js = "/assets/servicesapp/js/servicesapp.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "servicesapp/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Contract Master" : "public/js/contract_master.js",
    "Account Master" : "public/js/account_master.js",
    "Asset Master" : "public/js/asset_master.js",
    "Distributor Master" : "public/js/distributor_master.js",
    "Product Master" : "public/js/product_master.js",
    "Installation Request Master" : "public/js/installation_request_master.js",
    "Instrument Application Master" : "public/js/instrument_application_master.js",
    "Instrument Breakdown Master" : "public/js/instrument_breakdown_master.js",
    "PM Frequency Master" : "public/js/pm_frequency_master.js",
    "Other Calls Issue Master" : "public/js/other_calls_issue_master.js",
    "RR Application Call Master" : "public/js/rr_application_call_master.js",
    }

# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "servicesapp/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "servicesapp.utils.jinja_methods",
# 	"filters": "servicesapp.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "servicesapp.install.before_install"
# after_install = "servicesapp.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "servicesapp.uninstall.before_uninstall"
# after_uninstall = "servicesapp.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "servicesapp.utils.before_app_install"
# after_app_install = "servicesapp.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "servicesapp.utils.before_app_uninstall"
# after_app_uninstall = "servicesapp.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "servicesapp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }

permission_query_conditions = {
    "Instrument Application Master": "servicesapp.overwrite.permissions.service_engineer.instrument_application_permission",
    "Installation Request Master": "servicesapp.overwrite.permissions.service_engineer.installation_request_permission",
    "Instrument Breakdown Master": "servicesapp.overwrite.permissions.service_engineer.instrument_breakdown_permission",
    "RR Application Call Master": "servicesapp.overwrite.permissions.service_engineer.rr_application_call_permission",
    "Other Calls Issue Master": "servicesapp.overwrite.permissions.service_engineer.other_calls_issue_permission",
}

#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"servicesapp.tasks.all"
# 	],
# 	"daily": [
# 		"servicesapp.tasks.daily"
# 	],
# 	"hourly": [
# 		"servicesapp.tasks.hourly"
# 	],
# 	"weekly": [
# 		"servicesapp.tasks.weekly"
# 	],
# 	"monthly": [
# 		"servicesapp.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "servicesapp.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "servicesapp.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "servicesapp.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["servicesapp.utils.before_request"]
# after_request = ["servicesapp.utils.after_request"]

# Job Events
# ----------
# before_job = ["servicesapp.utils.before_job"]
# after_job = ["servicesapp.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"servicesapp.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

