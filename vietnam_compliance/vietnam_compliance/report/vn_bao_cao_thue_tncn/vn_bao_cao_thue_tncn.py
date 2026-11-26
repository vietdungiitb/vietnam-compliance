"""VN Báo Cáo Thuế TNCN — Personal Income Tax Report.

Summarizes monthly PIT per employee for a given date range.
Used to support form 05/KK-TNCN periodic declarations.

Kỳ được lọc theo **độ phủ giao kỳ** (`start <= to AND end >= from`), không phải
yêu cầu slip nằm gọn trong kỳ — nếu không, slip giao kỳ bị loại và tờ khai sai.
Không dùng raw SQL (S1); group trong Python để không phụ thuộc GROUP BY SQL.
"""

from __future__ import annotations

import frappe
from frappe import _


def execute(filters: dict | None = None) -> tuple[list[dict], list[dict]]:
    filters = filters or {}
    columns = [
        {"label": _("Mã NV"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": _("Họ tên"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": _("MST cá nhân"), "fieldname": "tax_code", "fieldtype": "Data", "width": 140},
        {"label": _("Tổng thu nhập"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 140},
        {"label": _("Giảm trừ"), "fieldname": "deductions", "fieldtype": "Currency", "width": 140},
        {"label": _("TN tính thuế"), "fieldname": "taxable_income", "fieldtype": "Currency", "width": 140},
        {"label": _("Thuế TNCN"), "fieldname": "pit", "fieldtype": "Currency", "width": 140},
    ]

    company = filters.get("company")
    if not company:
        frappe.throw(_("Vui lòng chọn công ty"))
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    if not from_date or not to_date:
        frappe.throw(_("Vui lòng chọn kỳ tính thuế (từ ngày / đến ngày)"))

    doc_filters: dict = {"docstatus": 1, "company": company}
    if from_date:
        doc_filters["start_date"] = ("<=", to_date)
    if to_date:
        doc_filters["end_date"] = (">=", from_date)

    slips = frappe.get_all(
        "Salary Slip",
        filters=doc_filters,
        fields=[
            "employee", "employee_name", "gross_pay", "total_deduction",
            "vn_taxable_income", "vn_pit_amount", "start_date", "end_date",
        ],
        order_by="employee_name, start_date",
    )

    grouped: dict[str, dict] = {}
    for slip in slips:
        key = slip.employee
        row = grouped.setdefault(key, {
            "employee": key,
            "employee_name": slip.employee_name,
            "gross_pay": 0.0,
            "deductions": 0.0,
            "taxable_income": 0.0,
            "pit": 0.0,
        })
        row["gross_pay"] += slip.gross_pay or 0
        row["deductions"] += slip.total_deduction or 0
        row["taxable_income"] += slip.vn_taxable_income or 0
        row["pit"] += slip.vn_pit_amount or 0

    data: list[dict] = []
    for row in grouped.values():
        row["tax_code"] = frappe.db.get_value("Employee", row["employee"], "vn_tax_code") or ""
        data.append(row)
    return columns, data
