"""VN Sổ Cái — Vietnamese-format General Ledger.

Renders GL Entries for a specific account with opening balance,
period activity, and running balance columns formatted per the
Vietnamese "Sổ cái" convention. Không dùng raw SQL (S1).
"""

from __future__ import annotations

import frappe
from frappe import _


def execute(filters: dict | None = None) -> tuple[list[dict], list[dict]]:
    filters = filters or {}
    columns = [
        {"label": _("Ngày"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Chứng từ"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 180},
        {"label": _("Diễn giải"), "fieldname": "remarks", "fieldtype": "Data", "width": 260},
        {"label": _("TK đối ứng"), "fieldname": "against_account", "fieldtype": "Data", "width": 160},
        {"label": _("Nợ"), "fieldname": "debit", "fieldtype": "Currency", "width": 130},
        {"label": _("Có"), "fieldname": "credit", "fieldtype": "Currency", "width": 130},
        {"label": _("Số dư"), "fieldname": "balance", "fieldtype": "Currency", "width": 140},
        {"label": _("Loại CT"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
    ]

    account = filters.get("account")
    if not account:
        frappe.throw(_("Vui lòng chọn tài khoản"))
    company = filters.get("company")
    if not company:
        # JS reqd không enforce được khi gọi trực tiếp API — phải chặn ở server.
        frappe.throw(_("Vui lòng chọn công ty"))

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    base_filters: dict = {
        "company": company,
        "account": account,
        "is_cancelled": 0,
    }
    opening_rows = (
        frappe.get_all(
            "GL Entry",
            filters={**base_filters, "posting_date": ("<", from_date)},
            fields=["debit", "credit"],
        )
        if from_date
        else []
    )
    opening_balance = float(
        sum((r.debit or 0) - (r.credit or 0) for r in opening_rows)
    )

    period_filters = dict(base_filters)
    if from_date:
        period_filters["posting_date"] = (">=", from_date)
    if to_date:
        period_filters["posting_date"] = ("<=", to_date)

    entries = frappe.get_all(
        "GL Entry",
        filters=period_filters,
        fields=[
            "posting_date", "voucher_type", "voucher_no",
            "against", "remarks", "debit", "credit",
        ],
        order_by="posting_date, creation",
    )

    data: list[dict] = [{
        "posting_date": from_date,
        "voucher_no": "",
        "remarks": _("Số dư đầu kỳ"),
        "against_account": "",
        "debit": opening_balance if opening_balance > 0 else 0,
        "credit": -opening_balance if opening_balance < 0 else 0,
        "balance": opening_balance,
        "voucher_type": "",
    }]

    balance = opening_balance
    for entry in entries:
        balance += (entry.debit or 0) - (entry.credit or 0)
        data.append({
            "posting_date": entry.posting_date,
            "voucher_type": entry.voucher_type,
            "voucher_no": entry.voucher_no,
            "remarks": entry.remarks or "",
            "against_account": entry.against or "",
            "debit": entry.debit or 0,
            "credit": entry.credit or 0,
            "balance": balance,
        })

    return columns, data
