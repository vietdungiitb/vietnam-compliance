"""VN Cân Đối Phát Sinh — Vietnamese Trial Balance.

Classic Vietnamese accounting trial-balance layout: for each non-group
account, shows opening balance (Nợ/Có), period movement (Nợ/Có), and
closing balance (Nợ/Có).

Không dùng raw SQL (S1): mọi truy vấn đi qua ``frappe.get_all``.
"""

from __future__ import annotations

import frappe
from frappe import _


def execute(filters: dict | None = None) -> tuple[list[dict], list[dict]]:
    filters = filters or {}
    company = filters.get("company")
    if not company:
        frappe.throw(_("Vui lòng chọn công ty"))

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    columns = [
        {"label": _("Số TK"), "fieldname": "account_number", "fieldtype": "Data", "width": 100},
        {"label": _("Tên tài khoản"), "fieldname": "account_name", "fieldtype": "Data", "width": 260},
        {"label": _("Dư đầu Nợ"), "fieldname": "opening_debit", "fieldtype": "Currency", "width": 130},
        {"label": _("Dư đầu Có"), "fieldname": "opening_credit", "fieldtype": "Currency", "width": 130},
        {"label": _("Phát sinh Nợ"), "fieldname": "period_debit", "fieldtype": "Currency", "width": 140},
        {"label": _("Phát sinh Có"), "fieldname": "period_credit", "fieldtype": "Currency", "width": 140},
        {"label": _("Dư cuối Nợ"), "fieldname": "closing_debit", "fieldtype": "Currency", "width": 130},
        {"label": _("Dư cuối Có"), "fieldname": "closing_credit", "fieldtype": "Currency", "width": 130},
    ]

    accounts = frappe.get_all(
        "Account",
        filters={"company": company, "is_group": 0, "disabled": 0},
        fields=["name", "account_name", "account_number"],
        order_by="account_number",
    )

    data: list[dict] = []
    for acc in accounts:
        opening_filters: dict = {
            "company": company,
            "account": acc.name,
            "is_cancelled": 0,
            "posting_date": ("<", from_date),
        }
        period_filters: dict = {
            "company": company,
            "account": acc.name,
            "is_cancelled": 0,
        }
        if from_date:
            period_filters["posting_date"] = (">=", from_date)
        if to_date:
            period_filters["posting_date"] = ("<=", to_date)

        opening_rows = (
            frappe.get_all(
                "GL Entry",
                filters=opening_filters,
                fields=["debit", "credit"],
            )
            if from_date
            else []
        )
        opening_bal = float(
            sum((r.debit or 0) - (r.credit or 0) for r in opening_rows)
        )

        period_rows = frappe.get_all(
            "GL Entry", filters=period_filters, fields=["debit", "credit"]
        )
        period_debit = float(sum((r.debit or 0) for r in period_rows))
        period_credit = float(sum((r.credit or 0) for r in period_rows))
        closing_bal = opening_bal + period_debit - period_credit

        # Bỏ qua tài khoản không có hoạt động và số dư bằng 0.
        if not any((opening_bal, period_debit, period_credit, closing_bal)):
            continue

        data.append({
            "account_number": acc.account_number or "",
            "account_name": acc.account_name,
            "opening_debit": opening_bal if opening_bal > 0 else 0,
            "opening_credit": -opening_bal if opening_bal < 0 else 0,
            "period_debit": period_debit,
            "period_credit": period_credit,
            "closing_debit": closing_bal if closing_bal > 0 else 0,
            "closing_credit": -closing_bal if closing_bal < 0 else 0,
        })

    return columns, data
