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
    frappe.db.commit()
    print(f"[qcs_akd] setup_company_defaults: cost centers ensured for {company}.")


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
