"""VN Bảng Cân Đối Kế Toán — B01-DN theo TT 99/2025 (khung cơ bản).

Không hard-code số tài khoản: dùng `Account.root_type` (Asset/Liability/Equity)
nên chạy được cho cả TT 99, TT 200 và TT 133. Không dùng raw SQL (S1).
Số dư lấy từ GL Entry đến `as_of`, đã loại bỏ chứng từ hủy.
"""

from __future__ import annotations

import frappe
from frappe import _


def execute(filters: dict | None = None) -> tuple[list[dict], list[dict]]:
    filters = filters or {}
    company = filters.get("company")
    if not company:
        frappe.throw(_("Vui lòng chọn công ty"))
    as_of = filters.get("as_of") or filters.get("to_date")
    if not as_of:
        frappe.throw(_("Vui lòng chọn ngày kết thúc"))

    columns = [
        {"label": _("Nhóm"), "fieldname": "group", "fieldtype": "Data", "width": 180},
        {"label": _("Số TK"), "fieldname": "account_number", "fieldtype": "Data", "width": 100},
        {"label": _("Tên tài khoản"), "fieldname": "account_name", "fieldtype": "Data", "width": 280},
        {"label": _("Số dư"), "fieldname": "balance", "fieldtype": "Currency", "width": 160},
    ]

    accounts = frappe.get_all(
        "Account",
        filters={
            "company": company,
            "is_group": 0,
            "disabled": 0,
            "root_type": ("in", ["Asset", "Liability", "Equity"]),
        },
        fields=["name", "account_number", "account_name", "root_type"],
        order_by="account_number",
    )

    data: list[dict] = []
    totals: dict[str, float] = {"Asset": 0.0, "Liability": 0.0, "Equity": 0.0}
    for acc in accounts:
        rows = frappe.get_all(
            "GL Entry",
            filters={
                "company": company,
                "account": acc.name,
                "is_cancelled": 0,
                "posting_date": ("<=", as_of),
            },
            fields=["debit", "credit"],
        )
        balance = float(sum((r.debit or 0) - (r.credit or 0) for r in rows))
        if not balance:
            continue
        group = {
            "Asset": _("Tài sản"),
            "Liability": _("Nợ phải trả"),
            "Equity": _("Vốn chủ sở hữu"),
        }[acc.root_type]
        totals[acc.root_type] += balance
        data.append({
            "group": group,
            "account_number": acc.account_number or "",
            "account_name": acc.account_name,
            "balance": balance if acc.root_type == "Asset" else -balance,
        })

    data.append({
        "group": _("TỔNG TÀI SẢN"),
        "account_number": "",
        "account_name": "",
        "balance": totals["Asset"],
    })
    data.append({
        "group": _("TỔNG NGUỒN VỐN"),
        "account_number": "",
        "account_name": "",
        "balance": totals["Liability"] + totals["Equity"],
    })
    return columns, data
