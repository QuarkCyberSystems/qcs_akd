"""
AKD Consulting LLC — initial fixtures.

Sourced from BRD v4 (24-Apr-2026). All operations are idempotent: safe to re-run.

Two entry points:
    after_install()                    — runs on `bench install-app qcs_akd`. Creates
                                         company-agnostic masters (Customer Groups,
                                         Territories, Supplier Groups, Item Groups,
                                         Payment Terms, Modes of Payment, Project
                                         Types, Asset Categories, Lead Sources,
                                         Quotation Lost Reasons).
    setup_company_defaults(company)    — call once per Company after creating it:
                                         `bench --site SITE execute qcs_akd.install.setup_company_defaults
                                          --kwargs '{"company":"AKD Consulting LLC"}'`
                                         Creates Cost Centers and wires Asset
                                         Category accounts that depend on the
                                         company's Chart of Accounts.
"""

import frappe


# ---------------------------------------------------------------------------
# Reference data (BRD-sourced)
# ---------------------------------------------------------------------------

CUSTOMER_GROUPS = [
    # FR-SELL-05/07 — hierarchical; explicit list pending AKD (FR-SELL-06 open).
    {"name": "Oil & Gas", "is_group": 0},
    {"name": "Utility", "is_group": 0},
    {"name": "Government", "is_group": 0},
    {"name": "Marine", "is_group": 0},
]

TERRITORIES = [
    # FR-SELL-14 — hierarchical (FR-SELL-15).
    {"name": "Africa", "is_group": 1, "parent_territory": "All Territories"},
    {"name": "Middle East", "is_group": 1, "parent_territory": "All Territories"},
]

SUPPLIER_GROUPS = [
    # FR-BUY-07/08
    {"name": "Indigenous"},
    {"name": "Foreign"},
    {"name": "Service Provider"},
    {"name": "Critical"},
    {"name": "Non-Critical"},
    {"name": "OEM"},
    {"name": "Non-OEM"},
]

ITEM_GROUPS = [
    # FR-BUY-06
    {"name": "Services"},
    {"name": "Capital Equipment"},
    {"name": "Consumables"},
    {"name": "Subcontracting"},
]

# FR-ACC-44 / FR-ACC-45
PAYMENT_TERMS = [
    {"payment_term_name": "PIA",      "credit_days": 0,  "invoice_portion": 100, "due_date_based_on": "Day(s) after invoice date"},
    {"payment_term_name": "Net 30",   "credit_days": 30, "invoice_portion": 100, "due_date_based_on": "Day(s) after invoice date"},
    {"payment_term_name": "Net 45",   "credit_days": 45, "invoice_portion": 100, "due_date_based_on": "Day(s) after invoice date"},
    {"payment_term_name": "Net 60",   "credit_days": 60, "invoice_portion": 100, "due_date_based_on": "Day(s) after invoice date"},
]

PAYMENT_TERMS_TEMPLATES = [
    # Customer-side (FR-ACC-44)
    {"name": "AKD Customer Net 30", "terms": [("Net 30", 100)]},
    {"name": "AKD Customer Net 45", "terms": [("Net 45", 100)]},
    {"name": "AKD Customer Net 60", "terms": [("Net 60", 100)]},
    # Supplier-side (FR-ACC-45)
    {"name": "AKD Supplier PIA",    "terms": [("PIA", 100)]},
    {"name": "AKD Supplier Net 30", "terms": [("Net 30", 100)]},
    {"name": "AKD Supplier Net 45", "terms": [("Net 45", 100)]},
    {"name": "AKD Supplier Net 60", "terms": [("Net 60", 100)]},
    # Split (FR-ACC-48)
    {"name": "AKD Split 50-50",     "terms": [("PIA", 50), ("Net 30", 50)]},
]

MODES_OF_PAYMENT = [
    # FR-ACC-46
    {"mode_of_payment": "Bank Transfer", "type": "Bank"},
    {"mode_of_payment": "Cheque",        "type": "Bank"},
]

PROJECT_TYPES = [
    # FR-PROJ-06
    {"name": "Advisory"},
    {"name": "AI"},
    {"name": "IT Implementation"},
]

ASSET_CATEGORIES = [
    # FR-FA-04, FR-FA-23, FR-FA-24, FR-FA-26
    {
        "asset_category_name": "Furniture",
        "total_number_of_depreciations": 20,   # 5 years × 4 quarters (FR-FA-23)
        "frequency_of_depreciation": 3,        # Quarterly (FR-FA-24)
        "depreciation_method": "Straight Line",
    },
    {
        "asset_category_name": "IT Equipment",
        "total_number_of_depreciations": 12,   # 3 years × 4 quarters
        "frequency_of_depreciation": 3,
        "depreciation_method": "Straight Line",
    },
]

LEAD_SOURCES = [
    # FR-CRM-06
    "Website", "Phone", "Walk-in", "Referral", "Social Media", "Email Campaign",
    "Trade Show / Event", "Paid Advertising", "Partner / Channel", "Cold Outreach",
]

QUOTATION_LOST_REASONS = [
    # FR-SELL-21 — sensible defaults; AKD can add more.
    "Price too high", "Lost to competitor", "Project cancelled",
    "Timing", "Technical fit", "No budget",
]

OPPORTUNITY_LOST_REASONS = [
    # FR-CRM-19
    "Price", "Competitor", "Timing", "Budget", "No decision", "Technical fit",
]

# AKD is a consulting/services company (FR-QA-11). Items are services or fixed
# assets, not stock. Customize the Item form so stock fields default off and hide.
ITEM_FORM_CUSTOMIZATIONS = [
    # (field_name, property, property_type, value)
    ("is_stock_item",                 "default", "Text", "0"),    # Maintain Stock = unchecked
    ("is_stock_item",                 "hidden",  "Check", "1"),    # hide the checkbox
    ("include_item_in_manufacturing", "default", "Text", "0"),    # no manufacturing
    ("include_item_in_manufacturing", "hidden",  "Check", "1"),
    ("is_sub_contracted_item",        "hidden",  "Check", "1"),    # subcontracting OOS per BRD
    ("has_serial_no",                 "hidden",  "Check", "1"),    # stock feature only
    ("has_batch_no",                  "hidden",  "Check", "1"),    # stock feature only
    ("has_variants",                  "hidden",  "Check", "1"),    # item variants overkill
]

# AKD default tax routing — every new Item should default to UAE VAT 5% / VAT-5;
# every new Customer should default to VAT-5 Tax Category. Saves users a click.
DEFAULT_TAX_CATEGORY     = "VAT-5"
DEFAULT_ITEM_TAX_TEMPLATE = "UAE VAT 5% - ACL"

ITEM_TAX_AUTOFILL_SCRIPT = """
// Auto-fill default Tax row on new Item (AKD VAT-5)
frappe.ui.form.on('Item', {
    refresh: function(frm) {
        if (frm.is_new() && (!frm.doc.taxes || frm.doc.taxes.length === 0)) {
            const row = frm.add_child('taxes');
            row.item_tax_template = 'UAE VAT 5% - ACL';
            row.tax_category = 'VAT-5';
            frm.refresh_field('taxes');
        }
    }
});
"""
ITEM_TAX_CLIENT_SCRIPT_NAME = "AKD Item Tax Default"

# Hide rarely-used / not-applicable fields from the 7 main transaction forms.
# Each row is (doctype, fieldname). Property Setter sets hidden=1.
# Naming Series is hidden because AKD uses Document Naming Rule instead.
# Stock-related fields hidden because AKD is a service company.
# Time Sheet List hidden on Sales Invoice — SO→SI flow auto-populates.
# Incoterm hidden — used internally if needed via Customize Form.
# From Date hidden — covered by posting_date.
AKD_CURRENCIES = ["AED", "USD", "EUR", "INR", "QAR", "SAR", "NGN", "GBP"]

# ---------------------------------------------------------------------------
# AKD Role Profiles + Module Profiles (Phase F8)
# ---------------------------------------------------------------------------
# Pre-packed role / module access bundles per AKD job function. Users are NOT
# created here (those go in cutover/scripts/phase_f8_users_and_profiles.py)
# because user accounts are per-deployment data. Profiles themselves should
# exist on every site so user creation via UI is one-click.

AKD_ROLE_PROFILES = {
    "AKD Accounts Manager":  ["Accounts Manager", "Accounts User", "Employee"],
    "AKD Purchase Manager":  ["Purchase Manager", "Purchase User", "Stock User", "Employee"],
    "AKD Purchase User":     ["Purchase User", "Stock User", "Employee"],
    "AKD Sales Lead":        ["Sales Manager", "Sales User", "Projects Manager",
                              "Projects User", "Quality Manager", "Quality Inspector",
                              "Employee"],
    "AKD Sales/Projects":    ["Sales User", "Projects User", "Employee"],
    "AKD Quality Lead":      ["Quality Manager", "Quality Inspector", "Employee"],
    "AKD System Admin":      ["System Manager", "Accounts Manager", "Sales Manager",
                              "Purchase Manager", "Projects Manager", "Quality Manager",
                              "Stock Manager", "HR Manager", "Employee"],
}

# Modules every AKD profile blocks (not in BRD scope).
# Slimmed list — Frappe framework modules (Core, Desk, Email, etc), framework
# integrations (Communication, Workflow, Setup, etc), and Quality Management
# are NOT blocked even when not in scope — blocking them breaks UI / notifications,
# and Quality Management is needed by Maureen/Subham.
AKD_ALWAYS_BLOCKED_MODULES = [
    "HR", "Payroll", "Education", "Healthcare", "Agriculture",
    "Loan Management", "Non Profit", "Marketplace", "Hospitality", "Lending",
]

# Per-profile extra blocks (on top of AKD_ALWAYS_BLOCKED_MODULES).
AKD_MODULE_PROFILES = {
    "AKD Accounting":     ["Selling", "Buying", "CRM", "Projects", "Stock"],
    "AKD Buying":         ["Selling", "CRM", "Projects", "Accounts", "Assets"],
    "AKD Sales Lead":     ["Buying", "Accounts", "Assets"],
    "AKD Sales/Projects": ["Buying", "Accounts", "Assets"],
    "AKD Quality":        ["Buying", "Selling", "Accounts", "Assets", "Projects", "CRM", "Stock"],
    "AKD System Admin":   [],   # full access
}

# Dynamic Letter Head — pulls branding from Company + linked Address + Bank Account
# (header logo, TRN, phone, email, website; footer: 3 offices + bank IBANs).
AKD_LETTER_HEAD_NAME = "AKD Letter Head"

AKD_LETTER_HEAD_HEADER = """\
{%- set company = doc.company or 'AKD Consulting LLC' -%}
{%- set co = frappe.db.get_value("Company", company, ["company_logo", "tax_id", "website", "email", "phone_no"], as_dict=True) -%}
<table style="width:100%;border-bottom:2px solid #1F4E78;padding-bottom:8px;margin-bottom:8px;">
  <tr>
    <td style="width:30%;vertical-align:middle;">
      {% if co and co.company_logo %}
        <img src="{{ co.company_logo }}" style="height:60px;"/>
      {% else %}
        <h2 style="margin:0;color:#1F4E78;">{{ company }}</h2>
      {% endif %}
    </td>
    <td style="text-align:right;vertical-align:middle;font-size:10px;color:#333;line-height:1.4;">
      <b style="color:#1F4E78;font-size:11px;">{{ company }}</b><br/>
      {% if co and co.tax_id %}TRN: {{ co.tax_id }} | License: 1403338<br/>{% endif %}
      {% if co and co.phone_no %}Tel: {{ co.phone_no }}{% endif %}
      {% if co and co.email %} | {{ co.email }}{% endif %}<br/>
      {% if co and co.website %}{{ co.website }}{% endif %}
    </td>
  </tr>
</table>
"""

AKD_LETTER_HEAD_FOOTER = """\
{%- set company = doc.company or 'AKD Consulting LLC' -%}
{%- set address_names = frappe.get_all("Dynamic Link", filters={"link_doctype":"Company","link_name":company,"parenttype":"Address"}, pluck="parent") -%}
{%- set bank_accounts = frappe.get_all("Bank Account", filters={"company":company,"is_company_account":1,"disabled":0}, fields=["account_name","iban","bank"]) -%}
<div style="font-size:8px;color:#555;border-top:1px solid #ccc;padding-top:6px;margin-top:8px;">
  <table style="width:100%;font-size:8px;line-height:1.3;">
    <tr>
      {% for an in address_names %}
        {%- set a = frappe.db.get_value("Address", an, ["address_title","address_line1","address_line2","city","country","phone"], as_dict=True) -%}
        {% if a %}
        <td style="padding:4px 8px;vertical-align:top;width:33%;">
          <b style="color:#1F4E78;">{{ a.address_title }}</b><br/>
          {{ a.address_line1 }}{% if a.address_line2 %}<br/>{{ a.address_line2 }}{% endif %}<br/>
          {{ a.city }}{% if a.country %}, {{ a.country }}{% endif %}
          {% if a.phone %}<br/>Tel: {{ a.phone }}{% endif %}
        </td>
        {% endif %}
      {% endfor %}
    </tr>
  </table>
  {% if bank_accounts %}
  <div style="margin-top:6px;text-align:center;border-top:1px dotted #ddd;padding-top:4px;">
    {% for b in bank_accounts %}
      <b>{{ b.account_name }}</b> · IBAN {{ b.iban or '-' }} · SWIFT {{ frappe.db.get_value("Bank", b.bank, "swift_number") or '-' }}{% if not loop.last %} &nbsp;|&nbsp; {% endif %}
    {% endfor %}
  </div>
  {% endif %}
</div>
"""
# NGN — Nigeria operations (Port Harcourt + Abuja offices, FR-BUY-74 + FR-SELL-50)
# GBP — international supplier currency per FR-BUY-74

TXN_FIELDS_TO_HIDE = [
    # naming_series — all 7
    ("Sales Invoice",    "naming_series"),
    ("Delivery Note",    "naming_series"),
    ("Sales Order",      "naming_series"),
    ("Quotation",        "naming_series"),
    ("Purchase Invoice", "naming_series"),
    ("Purchase Receipt", "naming_series"),
    ("Purchase Order",   "naming_series"),
    # scan_barcode — all 7
    ("Sales Invoice",    "scan_barcode"),
    ("Delivery Note",    "scan_barcode"),
    ("Sales Order",      "scan_barcode"),
    ("Quotation",        "scan_barcode"),
    ("Purchase Invoice", "scan_barcode"),
    ("Purchase Receipt", "scan_barcode"),
    ("Purchase Order",   "scan_barcode"),
    # last_scanned_warehouse — appears alongside scan_barcode (all 7)
    ("Sales Invoice",    "last_scanned_warehouse"),
    ("Delivery Note",    "last_scanned_warehouse"),
    ("Sales Order",      "last_scanned_warehouse"),
    ("Quotation",        "last_scanned_warehouse"),
    ("Purchase Invoice", "last_scanned_warehouse"),
    ("Purchase Receipt", "last_scanned_warehouse"),
    ("Purchase Order",   "last_scanned_warehouse"),
    # update_stock — SI + PI only
    ("Sales Invoice",    "update_stock"),
    ("Purchase Invoice", "update_stock"),
    # shipping_rule — all 7
    ("Sales Invoice",    "shipping_rule"),
    ("Delivery Note",    "shipping_rule"),
    ("Sales Order",      "shipping_rule"),
    ("Quotation",        "shipping_rule"),
    ("Purchase Invoice", "shipping_rule"),
    ("Purchase Receipt", "shipping_rule"),
    ("Purchase Order",   "shipping_rule"),
    # incoterm — all 7
    ("Sales Invoice",    "incoterm"),
    ("Delivery Note",    "incoterm"),
    ("Sales Order",      "incoterm"),
    ("Quotation",        "incoterm"),
    ("Purchase Invoice", "incoterm"),
    ("Purchase Receipt", "incoterm"),
    ("Purchase Order",   "incoterm"),
    # timesheets — Sales Invoice only
    ("Sales Invoice",    "timesheets"),
    # from_date — SI / SO / PI / PO
    ("Sales Invoice",    "from_date"),
    ("Sales Order",      "from_date"),
    ("Purchase Invoice", "from_date"),
    ("Purchase Order",   "from_date"),
]


# ---------------------------------------------------------------------------
# after_install — runs on `bench install-app qcs_akd`
# ---------------------------------------------------------------------------

def after_install():
    """Create company-agnostic masters. Idempotent + resilient — a failure in
    one fixture (e.g. a doctype missing on this Frappe version) does not block
    the rest from installing."""
    frappe.flags.in_install = True
    fixtures = [
        _ensure_payment_terms,
        _ensure_payment_terms_templates,
        _ensure_modes_of_payment,
        _ensure_customer_groups,
        _ensure_territories,
        _ensure_supplier_groups,
        _ensure_item_groups,
        _ensure_project_types,
        _ensure_asset_categories,
        _ensure_lead_sources,
        _ensure_quotation_lost_reasons,
        _ensure_opportunity_lost_reasons,
        _ensure_item_form_customizations,
        _ensure_customer_tax_category_default,
        _ensure_item_tax_autofill_script,
        _ensure_txn_fields_hidden,
        _ensure_akd_currencies_enabled,
        _ensure_akd_letter_head,
        _ensure_akd_role_profiles,
        _ensure_akd_module_profiles,
        _ensure_default_print_formats,
        _ensure_crm_permission_scripts,
    ]
    skipped = []
    try:
        for fn in fixtures:
            try:
                fn()
            except Exception as e:
                # Doctype missing on this Frappe version, or other recoverable
                # issue — log and continue so other fixtures still apply.
                skipped.append(f"{fn.__name__}: {type(e).__name__}: {e}")
                print(f"[qcs_akd] ⚠ {fn.__name__} skipped: {type(e).__name__}: {e}")
                frappe.db.rollback()
        frappe.db.commit()
        print(f"[qcs_akd] after_install: {len(fixtures) - len(skipped)}/{len(fixtures)} fixtures applied; {len(skipped)} skipped.")
    finally:
        frappe.flags.in_install = False


def setup_company_defaults(company):
    """Create company-scoped masters: Cost Centers + wire Asset Category accounts.

    Call after the Company DocType has been created and Chart of Accounts imported.
    Idempotent.
    """
    if not frappe.db.exists("Company", company):
        frappe.throw(f"Company '{company}' does not exist. Create it first.")
    _ensure_cost_centers(company)
    _ensure_service_company_settings(company)
    frappe.db.commit()
    print(f"[qcs_akd] setup_company_defaults: cost centers + service-company settings ensured for {company}.")


def _ensure_service_company_settings(company):
    """AKD is a service company: perpetual inventory must be OFF (otherwise
    Purchase Invoices on non-stock items demand a 'Stock Received But Not Billed'
    account that doesn't exist). Surfaced by the G2 workflow smoke test.
    Idempotent — only writes if currently enabled."""
    if frappe.db.get_value("Company", company, "enable_perpetual_inventory"):
        frappe.db.set_value("Company", company, "enable_perpetual_inventory", 0)


# ---------------------------------------------------------------------------
# Helpers — every helper is idempotent
# ---------------------------------------------------------------------------

def _ensure_payment_terms():
    for t in PAYMENT_TERMS:
        name = t["payment_term_name"]
        if frappe.db.exists("Payment Term", name):
            continue
        doc = frappe.new_doc("Payment Term")
        doc.update(t)
        doc.insert(ignore_permissions=True)


def _ensure_payment_terms_templates():
    for tmpl in PAYMENT_TERMS_TEMPLATES:
        if frappe.db.exists("Payment Terms Template", tmpl["name"]):
            continue
        doc = frappe.new_doc("Payment Terms Template")
        doc.template_name = tmpl["name"]
        for term_name, portion in tmpl["terms"]:
            doc.append("terms", {
                "payment_term": term_name,
                "invoice_portion": portion,
                "due_date_based_on": "Day(s) after invoice date",
                "credit_days": frappe.db.get_value("Payment Term", term_name, "credit_days") or 0,
            })
        doc.insert(ignore_permissions=True)


def _ensure_modes_of_payment():
    for m in MODES_OF_PAYMENT:
        if frappe.db.exists("Mode of Payment", m["mode_of_payment"]):
            continue
        doc = frappe.new_doc("Mode of Payment")
        doc.update(m)
        doc.insert(ignore_permissions=True)


def _ensure_customer_groups():
    parent = "All Customer Groups"
    for g in CUSTOMER_GROUPS:
        if frappe.db.exists("Customer Group", g["name"]):
            continue
        doc = frappe.new_doc("Customer Group")
        doc.customer_group_name = g["name"]
        doc.parent_customer_group = parent
        doc.is_group = g.get("is_group", 0)
        doc.insert(ignore_permissions=True)


def _ensure_territories():
    for t in TERRITORIES:
        if frappe.db.exists("Territory", t["name"]):
            continue
        doc = frappe.new_doc("Territory")
        doc.territory_name = t["name"]
        doc.parent_territory = t.get("parent_territory", "All Territories")
        doc.is_group = t.get("is_group", 0)
        doc.insert(ignore_permissions=True)


def _ensure_supplier_groups():
    parent = "All Supplier Groups"
    for g in SUPPLIER_GROUPS:
        if frappe.db.exists("Supplier Group", g["name"]):
            continue
        doc = frappe.new_doc("Supplier Group")
        doc.supplier_group_name = g["name"]
        doc.parent_supplier_group = parent
        doc.insert(ignore_permissions=True)


def _ensure_item_groups():
    parent = "All Item Groups"
    for g in ITEM_GROUPS:
        if frappe.db.exists("Item Group", g["name"]):
            continue
        doc = frappe.new_doc("Item Group")
        doc.item_group_name = g["name"]
        doc.parent_item_group = parent
        doc.insert(ignore_permissions=True)


def _ensure_project_types():
    for p in PROJECT_TYPES:
        if frappe.db.exists("Project Type", p["name"]):
            continue
        doc = frappe.new_doc("Project Type")
        doc.project_type = p["name"]
        doc.insert(ignore_permissions=True)


def _ensure_asset_categories():
    for c in ASSET_CATEGORIES:
        if frappe.db.exists("Asset Category", c["asset_category_name"]):
            continue
        doc = frappe.new_doc("Asset Category")
        doc.asset_category_name = c["asset_category_name"]
        doc.total_number_of_depreciations = c["total_number_of_depreciations"]
        doc.frequency_of_depreciation = c["frequency_of_depreciation"]
        doc.depreciation_method = c["depreciation_method"]
        doc.insert(ignore_permissions=True)


def _doctype_loadable(doctype):
    """True if both the DocType record exists AND its Python controller can be
    imported. Newer Frappe versions move some doctypes (e.g. Lead Source)
    out to separate CRM apps — skip cleanly when the controller is missing."""
    if not frappe.db.exists("DocType", doctype):
        return False
    try:
        frappe.get_meta(doctype)
        return True
    except (ImportError, ModuleNotFoundError):
        return False


def _ensure_lead_sources():
    if not _doctype_loadable("Lead Source"):
        print("[qcs_akd] Lead Source doctype not loadable on this Frappe version — skipping")
        return
    for src in LEAD_SOURCES:
        if frappe.db.exists("Lead Source", src):
            continue
        doc = frappe.new_doc("Lead Source")
        doc.source_name = src
        doc.insert(ignore_permissions=True)


def _ensure_quotation_lost_reasons():
    if not _doctype_loadable("Quotation Lost Reason"):
        print("[qcs_akd] Quotation Lost Reason doctype not loadable — skipping")
        return
    for r in QUOTATION_LOST_REASONS:
        if frappe.db.exists("Quotation Lost Reason", r):
            continue
        doc = frappe.new_doc("Quotation Lost Reason")
        doc.order_lost_reason = r
        doc.insert(ignore_permissions=True)


def _ensure_opportunity_lost_reasons():
    if not _doctype_loadable("Opportunity Lost Reason"):
        print("[qcs_akd] Opportunity Lost Reason doctype not loadable — skipping")
        return
    for r in OPPORTUNITY_LOST_REASONS:
        if frappe.db.exists("Opportunity Lost Reason", r):
            continue
        doc = frappe.new_doc("Opportunity Lost Reason")
        doc.lost_reason = r
        doc.insert(ignore_permissions=True)


def _ensure_item_form_customizations():
    """Service-company Item form: stock fields hidden + Maintain Stock defaults off."""
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    for field_name, prop, prop_type, value in ITEM_FORM_CUSTOMIZATIONS:
        ps_name = f"Item-{field_name}-{prop}"
        if frappe.db.exists("Property Setter", ps_name):
            continue
        make_property_setter("Item", field_name, prop, value, prop_type,
                              for_doctype=False, validate_fields_for_doctype=False)


def _ensure_customer_tax_category_default():
    """Customer.tax_category defaults to VAT-5 (saves a click on every new customer)."""
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    ps_name = "Customer-tax_category-default"
    if frappe.db.exists("Property Setter", ps_name):
        return
    if not frappe.db.exists("Tax Category", DEFAULT_TAX_CATEGORY):
        print(f"[qcs_akd] Tax Category '{DEFAULT_TAX_CATEGORY}' not found — skipping Customer default")
        return
    make_property_setter("Customer", "tax_category", "default", DEFAULT_TAX_CATEGORY,
                          "Link", for_doctype=False, validate_fields_for_doctype=False)


def _ensure_item_tax_autofill_script():
    """Client Script: when a new Item is opened, auto-append a Tax row with
    UAE VAT 5% - ACL + VAT-5. Skips on Items that already have a Tax row."""
    if not frappe.db.exists("Client Script", ITEM_TAX_CLIENT_SCRIPT_NAME):
        if not frappe.db.exists("Item Tax Template", DEFAULT_ITEM_TAX_TEMPLATE):
            print(f"[qcs_akd] Item Tax Template '{DEFAULT_ITEM_TAX_TEMPLATE}' not found — skipping autofill script")
            return
        doc = frappe.new_doc("Client Script")
        doc.name = ITEM_TAX_CLIENT_SCRIPT_NAME
        doc.dt = "Item"
        doc.view = "Form"
        doc.enabled = 1
        doc.script = ITEM_TAX_AUTOFILL_SCRIPT
        doc.insert(ignore_permissions=True)
    _ensure_item_tax_server_script()


# Client Scripts only run in the browser — Items created via REST API or Data
# Import bypass them (bit us in the G1 masters import: 5 items landed with no
# taxes row). This Server Script fires on every save path.
ITEM_TAX_SERVER_SCRIPT_NAME = "AKD Item Tax Default (server)"
ITEM_TAX_SERVER_SCRIPT = """# Ensure every Item carries the default AKD tax row (works for UI + API + import).
# Client Script 'AKD Item Tax Default' gives instant UI feedback; this is the safety net.
template = "UAE VAT 5% - ACL"
category = "VAT-5"
if frappe.db.exists("Item Tax Template", template):
    rows = doc.get("taxes") or []
    has_template = False
    for t in rows:
        if t.item_tax_template == template:
            has_template = True
            if not t.tax_category:
                t.tax_category = category
    if not has_template:
        doc.append("taxes", {"item_tax_template": template, "tax_category": category})
"""


def _ensure_item_tax_server_script():
    if frappe.db.exists("Server Script", ITEM_TAX_SERVER_SCRIPT_NAME):
        return
    doc = frappe.new_doc("Server Script")
    doc.name = ITEM_TAX_SERVER_SCRIPT_NAME
    doc.script_type = "DocType Event"
    doc.reference_doctype = "Item"
    doc.doctype_event = "Before Save"
    doc.disabled = 0
    doc.script = ITEM_TAX_SERVER_SCRIPT
    doc.insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# CRM rep-sees-own permission filters (FR-CRM-64/65) — Phase G7
# ---------------------------------------------------------------------------
# Permission Query Server Scripts: sales reps see only Leads/Opportunities they
# own, created, or are assigned to. Sales Manager / System Manager / Accounts
# Manager (and Administrator) see everything.
#
# SANDBOX GOTCHA: frappe.get_roles is NOT exposed in the Server Script safe
# environment (AttributeError broke every Lead list on first deploy). Role
# membership must be checked via frappe.get_all on the Has Role child table.
# List-view filtering only — direct URL access isn't blocked (accepted v1).

CRM_PERMISSION_SCRIPTS = {
    "AKD Lead Own-Records Filter": ("Lead", """# FR-CRM-64/65 — sales reps see only their own Leads.
user = frappe.session.user
if user == "Administrator":
    conditions = ""
else:
    is_mgr = frappe.get_all("Has Role", filters={"parenttype": "User", "parent": user,
        "role": ["in", ["Sales Manager", "System Manager", "Accounts Manager"]]}, limit=1)
    if is_mgr:
        conditions = ""
    else:
        u = frappe.db.escape(user)
        a = frappe.db.escape("%" + user + "%")
        conditions = "(`tabLead`.lead_owner = " + u + " or `tabLead`.owner = " + u + " or ifnull(`tabLead`._assign,'') like " + a + ")"
"""),
    "AKD Opportunity Own-Records Filter": ("Opportunity", """# FR-CRM-64/65 — sales reps see only their own Opportunities.
user = frappe.session.user
if user == "Administrator":
    conditions = ""
else:
    is_mgr = frappe.get_all("Has Role", filters={"parenttype": "User", "parent": user,
        "role": ["in", ["Sales Manager", "System Manager", "Accounts Manager"]]}, limit=1)
    if is_mgr:
        conditions = ""
    else:
        u = frappe.db.escape(user)
        a = frappe.db.escape("%" + user + "%")
        conditions = "(`tabOpportunity`.owner = " + u + " or ifnull(`tabOpportunity`._assign,'') like " + a + ")"
"""),
}


def _ensure_crm_permission_scripts():
    """Create/refresh the 2 Permission Query scripts. Updates the script body if
    it drifts from this file — install.py is the source of truth."""
    for name, (ref_doctype, script) in CRM_PERMISSION_SCRIPTS.items():
        if frappe.db.exists("Server Script", name):
            if frappe.db.get_value("Server Script", name, "script") != script:
                frappe.db.set_value("Server Script", name, "script", script)
            continue
        doc = frappe.new_doc("Server Script")
        doc.name = name
        doc.script_type = "Permission Query"
        doc.reference_doctype = ref_doctype
        doc.disabled = 0
        doc.script = script
        doc.insert(ignore_permissions=True)


def _ensure_txn_fields_hidden():
    """Hide rarely-used / not-applicable fields on the 7 main transaction forms.
    See TXN_FIELDS_TO_HIDE for the matrix. Property Setter per (doctype, field).

    Defensive: if a Property Setter already exists but its value != '1' (e.g. a
    prior customization set hidden=0 — which actively UN-hides), update it to '1'."""
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    for doctype, field in TXN_FIELDS_TO_HIDE:
        ps_name = f"{doctype}-{field}-hidden"
        if frappe.db.exists("Property Setter", ps_name):
            current = frappe.db.get_value("Property Setter", ps_name, "value")
            if str(current) != "1":
                frappe.db.set_value("Property Setter", ps_name, "value", "1")
                print(f"[qcs_akd] ⤴ fixed {doctype}.{field}  (was {current!r} → 1)")
            continue
        try:
            make_property_setter(doctype, field, "hidden", "1", "Check",
                                  for_doctype=False, validate_fields_for_doctype=False)
        except Exception as e:
            print(f"[qcs_akd] hide {doctype}.{field}: {type(e).__name__}: {e}")
    _ensure_naming_series_defaults()


# naming_series is reqd=1 in core, and Frappe rejects a field that is
# hidden + mandatory + no default ("Field Series in row N cannot be hidden and
# mandatory without default"). Since F5 hides Series on the 7 transaction forms,
# each needs a default = its standard series. Harmless for naming — the AKD
# Document Naming Rules still override and produce AKD-SO-2026-... names.
NAMING_SERIES_DEFAULTS = {
    "Sales Invoice":    "ACC-SINV-.YYYY.-",
    "Delivery Note":    "MAT-DN-.YYYY.-",
    "Sales Order":      "SAL-ORD-.YYYY.-",
    "Quotation":        "SAL-QTN-.YYYY.-",
    "Purchase Invoice": "ACC-PINV-.YYYY.-",
    "Purchase Receipt": "MAT-PRE-.YYYY.-",
    "Purchase Order":   "PUR-ORD-.YYYY.-",
}


def _ensure_naming_series_defaults():
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    for doctype, series in NAMING_SERIES_DEFAULTS.items():
        existing = frappe.db.get_value(
            "Property Setter",
            {"doc_type": doctype, "field_name": "naming_series", "property": "default"},
            "name",
        )
        if existing:
            if frappe.db.get_value("Property Setter", existing, "value") != series:
                frappe.db.set_value("Property Setter", existing, "value", series)
            continue
        try:
            make_property_setter(doctype, "naming_series", "default", series, "Text",
                                  for_doctype=False, validate_fields_for_doctype=False)
        except Exception as e:
            print(f"[qcs_akd] naming_series default {doctype}: {type(e).__name__}: {e}")


def _ensure_akd_currencies_enabled():
    """Enable the currencies AKD operates in: AED, USD, EUR, INR, QAR, SAR.
    Exchange rates are seeded by `cutover/scripts/phase_f6_currency_exchange.py`
    on cut-over day (rates are time-sensitive — exchangerate.host auto-fetch
    keeps them refreshed afterwards)."""
    for cur in AKD_CURRENCIES:
        if not frappe.db.exists("Currency", cur):
            continue
        if frappe.db.get_value("Currency", cur, "enabled") == 1:
            continue
        frappe.db.set_value("Currency", cur, "enabled", 1)


def _ensure_akd_letter_head():
    """Create/refresh the dynamic AKD Letter Head — Jinja-driven from Company,
    linked Addresses, and Bank Account doctype. Always re-syncs templates so
    template improvements ship with the app."""
    if frappe.db.exists("Letter Head", AKD_LETTER_HEAD_NAME):
        lh = frappe.get_doc("Letter Head", AKD_LETTER_HEAD_NAME)
        lh.source = "HTML"
        lh.content = AKD_LETTER_HEAD_HEADER
        lh.footer_source = "HTML"
        lh.footer = AKD_LETTER_HEAD_FOOTER
        lh.is_default = 1
        lh.save(ignore_permissions=True)
        return
    doc = frappe.new_doc("Letter Head")
    doc.letter_head_name = AKD_LETTER_HEAD_NAME
    doc.is_default = 1
    doc.source = "HTML"
    doc.content = AKD_LETTER_HEAD_HEADER
    doc.footer_source = "HTML"
    doc.footer = AKD_LETTER_HEAD_FOOTER
    doc.insert(ignore_permissions=True)


def _ensure_cost_centers(company):
    """Cost centers: Sales, Admin, Finance, HR (FR-ACC-12). Flat structure (FR-ACC-13)."""
    abbr = frappe.db.get_value("Company", company, "abbr")
    if not abbr:
        frappe.throw(f"Company '{company}' has no abbreviation set.")
    parent = f"{company} - {abbr}"
    if not frappe.db.exists("Cost Center", parent):
        frappe.throw(f"Root cost center '{parent}' missing — has CoA been created for {company}?")

    for cc in ["Sales", "Admin", "Finance", "HR"]:
        full_name = f"{cc} - {abbr}"
        if frappe.db.exists("Cost Center", full_name):
            continue
        doc = frappe.new_doc("Cost Center")
        doc.cost_center_name = cc
        doc.parent_cost_center = parent
        doc.company = company
        doc.is_group = 0
        doc.insert(ignore_permissions=True)


def _ensure_akd_role_profiles():
    """Create 7 'AKD ...' Role Profiles bundling standard ERPNext roles per job function."""
    for name, roles in AKD_ROLE_PROFILES.items():
        if frappe.db.exists("Role Profile", name):
            continue
        doc = frappe.new_doc("Role Profile")
        doc.role_profile = name
        for r in roles:
            if frappe.db.exists("Role", r):
                doc.append("roles", {"role": r})
        doc.insert(ignore_permissions=True)


def _ensure_akd_module_profiles():
    """Create 7 'AKD ...' Module Profiles using block-list approach (16 always-blocked
    modules + per-profile extras). System Admin profile blocks nothing extra."""
    for name, extra_blocks in AKD_MODULE_PROFILES.items():
        if frappe.db.exists("Module Profile", name):
            continue
        doc = frappe.new_doc("Module Profile")
        doc.module_profile_name = name
        for m in (AKD_ALWAYS_BLOCKED_MODULES + extra_blocks):
            doc.append("block_modules", {"module": m})
        doc.insert(ignore_permissions=True)


# Per-doctype default print format → the branded AKD format.
# Implemented via Property Setter (property='default_print_format') so users get
# the AKD layout automatically when they hit Print. Only applies if the AKD
# print format exists (shipped under qcs_akd/print_format/).
AKD_DEFAULT_PRINT_FORMATS = {
    "Quotation":             "AKD Quotation",
    "Sales Order":           "AKD Sales Order",
    "Sales Invoice":         "AKD Sales Invoice",
    "Delivery Note":         "AKD Delivery Note",
    "Request for Quotation": "AKD Request for Quotation",
    "Purchase Order":        "AKD Purchase Order",
    "Purchase Receipt":      "AKD Purchase Receipt",
    "Purchase Invoice":      "AKD Purchase Invoice",
}


def _ensure_default_print_formats():
    """Set the AKD branded print format as the default per transaction doctype.
    Idempotent: updates the existing default_print_format Property Setter if present,
    else creates one. Skips a doctype whose AKD print format isn't installed."""
    for dt, pf in AKD_DEFAULT_PRINT_FORMATS.items():
        if not frappe.db.exists("Print Format", pf):
            continue
        existing = frappe.db.get_value(
            "Property Setter",
            {"doc_type": dt, "property": "default_print_format"},
            "name",
        )
        if existing:
            frappe.db.set_value("Property Setter", existing, "value", pf)
            continue
        frappe.get_doc({
            "doctype":          "Property Setter",
            "doctype_or_field": "DocType",
            "doc_type":         dt,
            "property":         "default_print_format",
            "property_type":    "Data",
            "value":            pf,
        }).insert(ignore_permissions=True)
