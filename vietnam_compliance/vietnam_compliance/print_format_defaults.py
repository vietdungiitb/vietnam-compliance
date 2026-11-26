"""Set Vietnamese print formats as default for the relevant DocTypes (F-10).

Vì sao cần: without this, a fresh site keeps ERPNext "Classic" as default, so
the VN templates (KCT note, CSS, payment reason) are never rendered unless a
user manually selects them. Idempotent Property Setter upsert, gated on the
Company's country being Vietnam — do not change defaults for non-VN companies.
"""

from __future__ import annotations

from typing import Any

#: DocType -> exact VN Print Format name.
VN_DEFAULT_FORMATS: dict[str, str] = {
    "Sales Invoice": "VN Hóa Đơn Bán Hàng",
    "Payment Entry": "VN Phiếu Thu",
    "Purchase Invoice": "VN Hóa Đơn Mua Hàng",
    "Quotation": "VN Báo Giá",
}


def _print_format_exists(name: str) -> bool:
    """Check the VN print format exists before pointing a default at it."""
    import frappe

    try:
        return bool(frappe.db.exists("Print Format", name))
    except Exception:  # noqa: BLE001 - stub/test without DB
        return False


def _company_is_vietnam(company: str | None) -> bool:
    """Only apply VN defaults when the company country is Vietnam.

    Missing country is treated as Vietnam for the default company so first-run
    setup works — but an explicitly non-VN country is never touched.
    """
    import frappe

    if not company:
        return True
    try:
        country = str(frappe.db.get_value("Company", company, "country") or "").strip()
    except Exception:  # noqa: BLE001
        return True
    return (not country) or country.lower() in {"vietnam", "viet nam", "vn"}


def set_default_print_formats(company: str | None = None) -> dict[str, Any]:
    """Upsert `default_print_format` Property Setters for VN DocTypes.

    Returns a summary with applied / skipped names — read-only callers can assert.
    """
    import frappe

    if not _company_is_vietnam(company):
        return {
            "applied": [],
            "skipped": list(VN_DEFAULT_FORMATS),
            "reason": "non-vn-company",
        }

    applied: list[str] = []
    skipped: list[str] = []
    for doctype, format_name in VN_DEFAULT_FORMATS.items():
        if not _print_format_exists(format_name):
            skipped.append(doctype)
            continue
        # Cùng filter với hook `ensure_vn_print_format_defaults` của
        # smart_edu_core để hai bản ghi hội tụ thành MỘT Property Setter.
        filters = {
            "doctype_or_field": "DocType",
            "doc_type": doctype,
            "field_name": "",
            "property": "default_print_format",
        }
        try:
            existing = frappe.db.get_value("Property Setter", filters, "name")
            if existing:
                frappe.db.set_value("Property Setter", existing, "value", format_name)
            else:
                frappe.get_doc(
                    {"doctype": "Property Setter", **filters,
                     "property_type": "Data", "value": format_name}
                ).insert(ignore_permissions=True)
                # S4: chạy lúc after_install (system hook); API key riêng
                # CHƯA CHẠY (Ops cấp service account — PLAN R-OPS);
                # audit log = Version của Property Setter trên site.
            applied.append(doctype)
        except Exception:  # noqa: BLE001 - one failure must not stop the rest
            skipped.append(doctype)
    return {"applied": applied, "skipped": skipped}


__all__ = ["VN_DEFAULT_FORMATS", "set_default_print_formats"]
