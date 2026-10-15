"""Frappe app hooks for vietnam_compliance (Vietnam Compliance Localization).

This module registers all integration points with Frappe/ERPNext:
- Lifecycle hooks (after_install, before_uninstall)
- DocType event subscriptions (Sales Invoice, Salary Slip)
- Setup Wizard stages for Vietnam country
- Fixtures, Jinja helpers, regional overrides
- Scheduler tasks, client scripts
"""

app_name = "vietnam_compliance"
app_title = "Tuân thủ VN"
app_publisher = "Edusuccess & Open Source Contributors"
app_description = "Vietnam Statutory Compliance & Localization for Frappe / ERPNext v16"
app_email = "tech@edusuccess.vn"
app_license = "GPL-3.0"
app_icon = "octicon octicon-globe"
app_color = "#DA251D"  # Vietnamese flag red

# Hiển thị icon trên màn hình chuyển đổi ứng dụng Desk (App Switcher)
add_to_apps_screen = [
    {
        "name": "vietnam_compliance",
        "logo": "/assets/vietnam_compliance/images/vietnam.svg",
        "title": "Tuân thủ VN",
        "route": "/app/tuan-thu-vn",
    }
]

required_apps = ["frappe", "erpnext", "hrms"]

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

after_install = "vietnam_compliance.vietnam_compliance.setup.after_install"
before_uninstall = "vietnam_compliance.vietnam_compliance.setup.before_uninstall"

# ---------------------------------------------------------------------------
# Setup Wizard
# ---------------------------------------------------------------------------

setup_wizard_requires = "assets/vietnam_compliance/js/setup_wizard.js"
setup_wizard_stages = "vietnam_compliance.vietnam_compliance.setup.get_setup_stages"

# ---------------------------------------------------------------------------
# DocType Events
# ---------------------------------------------------------------------------

doc_events = {
    "Sales Invoice": {
        "on_submit": "vietnam_compliance.e_invoicing.utils.on_sales_invoice_submit",
        "on_cancel": "vietnam_compliance.e_invoicing.utils.on_sales_invoice_cancel",
    },
    "Salary Slip": {
        "validate": "vietnam_compliance.payroll.utils.validate_salary_slip",
    },
}

# ---------------------------------------------------------------------------
# Fixtures — exported via `bench export-fixtures` for this module
# ---------------------------------------------------------------------------

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["module", "=", "Vietnam Compliance"]],
    },
    {
        "dt": "Property Setter",
        "filters": [["module", "=", "Vietnam Compliance"]],
    },
]

# ---------------------------------------------------------------------------
# Jinja template helpers (available in Print Formats)
# ---------------------------------------------------------------------------

jinja = {
    "methods": [
        "vietnam_compliance.payroll.utils.so_tien_bang_chu",
        "vietnam_compliance.payroll.utils.format_vnd",
    ],
}

# ---------------------------------------------------------------------------
# Regional overrides — replace ERPNext defaults when country == "Vietnam"
# ---------------------------------------------------------------------------

regional_overrides = {
    "Vietnam": {
        "erpnext.controllers.taxes_and_totals.get_regional_round_off_accounts": (
            "vietnam_compliance.accounting.tax_templates.get_round_off_accounts"
        ),
    },
}

# ---------------------------------------------------------------------------
# Override ERPNext's CoA discovery to include TT99/TT200/TT133
# ---------------------------------------------------------------------------

override_whitelisted_methods = {
    "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country": (
        "vietnam_compliance.accounting.chart_of_accounts.get_charts_for_country"
    ),
}

# Apply CoA monkey-patch on every request and every session boot.
# `before_request` runs in every worker process before the request handler,
# guaranteeing the patch is applied before Company.on_update fires.
before_request = ["vietnam_compliance.accounting.chart_of_accounts.ensure_patched"]
boot_session = "vietnam_compliance.accounting.chart_of_accounts.ensure_patched"

# ---------------------------------------------------------------------------
# Website / URL rules
# ---------------------------------------------------------------------------

website_route_rules = []

# ---------------------------------------------------------------------------
# Scheduler — polls pending e-invoices hourly
# ---------------------------------------------------------------------------

scheduler_events = {
    "hourly": [
        "vietnam_compliance.e_invoicing.utils.poll_pending_invoices",
    ],
}

# ---------------------------------------------------------------------------
# Client scripts
# ---------------------------------------------------------------------------

doctype_js = {
    "Sales Invoice": "public/js/vn_einvoice.js",
}

# ---------------------------------------------------------------------------
# Global assets
# ---------------------------------------------------------------------------

app_include_css = ["/assets/vietnam_compliance/css/vn_print.css"]
app_include_js = []

# Optional overrides
override_doctype_class = {}
