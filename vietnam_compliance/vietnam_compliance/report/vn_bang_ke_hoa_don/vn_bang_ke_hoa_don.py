"""VN Bảng Kê Hóa Đơn — Invoice Register.

Lists Sales Invoices (or Purchase Invoices) for a period with VAT
breakdown. Supports the ``invoice_type`` filter to switch between
Sales ("Bán ra") and Purchase ("Mua vào"). Không dùng raw SQL (S1).
"""

from __future__ import annotations

import frappe
from frappe import _


def execute(filters: dict | None = None) -> tuple[list[dict], list[dict]]:
    filters = filters or {}
    columns = [
        {"label": _("STT"), "fieldname": "idx", "fieldtype": "Int", "width": 60},
        {"label": _("Ngày HĐ"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Số HĐ"), "fieldname": "invoice_no", "fieldtype": "Data", "width": 160},
        {"label": _("Ký hiệu"), "fieldname": "series_symbol", "fieldtype": "Data", "width": 100},
        {"label": _("Khách hàng / NCC"), "fieldname": "party", "fieldtype": "Data", "width": 220},
        {"label": _("MST"), "fieldname": "tax_id", "fieldtype": "Data", "width": 120},
        {"label": _("Giá trị trước thuế"), "fieldname": "net_total", "fieldtype": "Currency", "width": 140},
        {"label": _("Thuế suất"), "fieldname": "tax_rate", "fieldtype": "Percent", "width": 90},
        {"label": _("Tiền thuế"), "fieldname": "tax_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Tổng tiền"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 140},
    ]

    company = filters.get("company")
    if not company:
        frappe.throw(_("Vui lòng chọn công ty"))

    invoice_type = filters.get("invoice_type", "Sales")
    doctype = "Sales Invoice" if invoice_type == "Sales" else "Purchase Invoice"
    party_field = "customer_name" if invoice_type == "Sales" else "supplier_name"

    doc_filters: dict = {"docstatus": 1, "company": company}
    if filters.get("from_date"):
        doc_filters["posting_date"] = (">=", filters["from_date"])
    if filters.get("to_date"):
        doc_filters["posting_date"] = ("<=", filters["to_date"])

    fields = [
        "name", "posting_date", party_field, "tax_id",
        "net_total", "grand_total", "total_taxes_and_charges",
    ]
    if invoice_type == "Sales":
        # Dùng field thật, không dùng `AS` alias — frappe.get_all không đảm bảo
        # chấp nhận biểu thức trong danh sách field.
        fields.append("vn_einvoice_number")

    rows = frappe.get_all(
        doctype, filters=doc_filters, fields=fields,
        order_by="posting_date, name",
    )

    data: list[dict] = []
    for i, row in enumerate(rows, start=1):
        tax_total = row.total_taxes_and_charges or 0
        tax_rate = round(tax_total / row.net_total * 100, 2) if row.net_total else 0
        data.append({
            "idx": i,
            "posting_date": row.posting_date,
            "invoice_no": (row.get("vn_einvoice_number") or row.name),
            "series_symbol": "",
            "party": row.get(party_field) or "",
            "tax_id": row.tax_id or "",
            "net_total": row.net_total or 0,
            "tax_rate": tax_rate,
            "tax_amount": tax_total,
            "grand_total": row.grand_total or 0,
        })
    return columns, data
