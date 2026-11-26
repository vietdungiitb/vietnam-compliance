"""VN Báo Cáo Kết Quả Kinh Doanh — B02-DN theo TT 99/2025 (khung cơ bản).

Dùng `Account.root_type` (Income/Expense) nên không phụ thuộc vào số tài khoản
của TT 99/TT 200/TT 133. Không dùng raw SQL (S1).
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
    if not (from_date and to_date):
        frappe.throw(_("Vui lòng chọn kỳ báo cáo"))

    columns = [
        {"label": _("Nhóm"), "fieldname": "group", "fieldtype": "Data", "width": 180},
        {"label": _("Số TK"), "fieldname": "account_number", "fieldtype": "Data", "width": 100},
        {"label": _("Tên tài khoản"), "fieldname": "account_name", "fieldtype": "Data", "width": 280},
        {"label": _("Số tiền"), "fieldname": "amount", "fieldtype": "Currency", "width": 160},
    ]

    accounts = frappe.get_all(
        "Account",
        filters={
            "company": company,
            "is_group": 0,
            "disabled": 0,
            "root_type": ("in", ["Income", "Expense"]),
        },
        fields=["name", "account_number", "account_name", "root_type"],
        order_by="account_number",
    )

    data: list[dict] = []
    totals = {"Income": 0.0, "Expense": 0.0}
    for acc in accounts:
        rows = frappe.get_all(
            "GL Entry",
            filters={
                "company": company,
                "account": acc.name,
                "is_cancelled": 0,
                "posting_date": ("between", [from_date, to_date]),
            },
            fields=["debit", "credit"],
        )
        movement = float(sum((r.credit or 0) - (r.debit or 0) for r in rows))
        if not movement:
            continue
        amount = movement if acc.root_type == "Income" else -movement
        totals[acc.root_type] += amount
        data.append({
            "group": _("Doanh thu") if acc.root_type == "Income" else _("Chi phí"),
            "account_number": acc.account_number or "",
            "account_name": acc.account_name,
            "amount": amount,
        })

    data.append({
        "group": _("TỔNG DOANH THU"),
        "account_number": "",
        "account_name": "",
        "amount": totals["Income"],
    })
    data.append({
        "group": _("TỔNG CHI PHÍ"),
        "account_number": "",
        "account_name": "",
        "amount": totals["Expense"],
    })
    data.append({
        "group": _("LỢI NHUẬN TRƯỚC THUẾ"),
        "account_number": "",
        "account_name": "",
        "amount": totals["Income"] - totals["Expense"],
    })
    return columns, data
