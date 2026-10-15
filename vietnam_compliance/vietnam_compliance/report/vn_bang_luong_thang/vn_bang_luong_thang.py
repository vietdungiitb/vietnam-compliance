"""Bản vá cho report `VN Bảng Lương Tháng` của app `vietnam_compliance` (ERPNext v16).

File này KHÔNG nằm trong `smart_edu_core`. Nó được chép vào app vendor **lúc
build** bởi `apps/bench/vendor/vietnam_compliance_report_adapters.py`, theo đúng khuôn
ADR-0007/ADR-0008 (vá tạm, có assert, tự gỡ khi upstream sửa).

VÌ SAO PHẢI VÁ (đo 15/10/2026 trên staging, ERPNext 16.36.1):

1. **`ss.base` không tồn tại.**
       OperationalError: (1054, "Unknown column 'ss.base' in 'WHERE'")
   Đã liệt kê đủ **76 cột** của `tabSalary Slip`: **không cột nào chứa chuỗi
   "basic"**. ERPNext 16 chỉ có `base_gross_pay`, `base_net_pay`, `total_earnings`.
   Report của vendor viết cho ERPNext bản cũ, khi Salary Slip còn cột `base`.

2. **`r.name` luôn là `None`.** SQL của vendor KHÔNG SELECT `ss.name`, nhưng code
   lại viết `r.name if "name" in r else None` ⇒ `_component_total()` luôn trả `0`
   ⇒ ba cột BHXH/BHYT/BHTN **luôn bằng 0** dù có dữ liệu. Lỗi âm thầm, chưa lộ
   vì lỗi (1) chặn trước.

3. **`allowances = gross_pay - base`** — không có `base` thì phép trừ vô nghĩa.

VÌ SAO VIẾT LẠI BẰNG `get_all` CHỨ KHÔNG SỬA SQL:

`AGENTS.md §3.1` S1 cấm raw SQL. Bản vá cũng không được lách: dùng
`frappe.get_all` + gom nhóm bằng Python. Báo cáo lương theo tháng chỉ vài trăm
dòng ⇒ nạp vào RAM không tốn, và đổi lại code đọc được, review được, qua cổng.

VÌ SAO "LƯƠNG CƠ BẢN" LẤY TỪ `Salary Detail`:

Trên Salary Slip không có cột nào là lương cơ bản (xem lý do (1)). Nhưng bảng con
`tabSalary Detail` có dòng cho từng khoản cấu thành. Ta cộng các dòng Earning
có tên thuộc `BASIC_COMPONENTS_DEFAULT`.

Tập tên lấy từ **Site Config** (`edu_basic_salary_components`) chứ không hard-code
chết, vì mỗi doanh nghiệp đặt tên khoản lương cơ bản khác nhau. Mặc định lấy cả
hai tên đang có sẵn trên site: "Basic" và "Lương cơ bản".

GỠ BẢN VÁ NÀY KHI: `vietnam_compliance` sửa được cả ba lỗi trên. Script adapter tự phát
hiện (đọc nội dung file vendor) và **không** ghi đè nữa — nên nâng app là tự hết.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

# Khoản lương cơ bản — mặc định khi Site Config chưa đặt.
BASIC_COMPONENTS_DEFAULT = ("Basic", "Lương cơ bản")

# Khoản khấu trừ bảo hiểm người lao động. Ba tên này ĐÃ ĐO là tồn tại trên site
# (vietnam_compliance tạo sẵn), nên ghép trực tiếp từ Salary Detail là đúng — thay vì tự
# chia `vn_insurance_employee` theo tỉ lệ, vì tỉ lệ BHXH có thể khác theo nghề
# và theo hợp đồng; công thức chia cứng sẽ ra số sai mà vẫn trông hợp lý.
INSURANCE_COMPONENTS = (
    ("bhxh", "BHXH (NLĐ 8%)"),
    ("bhyt", "BHYT (NLĐ 1.5%)"),
    ("bhtn", "BHTN (NLĐ 1%)"),
)


def _basic_components() -> tuple[str, ...]:
    """Tập tên khoản lương cơ bản, đọc từ Site Config nếu có.

    Đọc config phải bọc `try`: site mới chưa đặt thì dùng mặc định, và thiếu
    config không được làm chết report.
    """
    try:
        raw = frappe.get_conf().get("edu_basic_salary_components") or ""
    except Exception:  # noqa: BLE001 — thiếu Site Config không được chặn báo cáo
        return BASIC_COMPONENTS_DEFAULT
    names = tuple(x.strip() for x in str(raw).split(",") if x.strip())
    return names or BASIC_COMPONENTS_DEFAULT


def _month_range(year: int, month: int) -> tuple[str, str]:
    """Khoảng ngày của tháng, dạng ISO. Tránh hàm SQL `MONTH()`/`YEAR()`."""
    from frappe.utils import get_last_day

    first = "%04d-%02d-01" % (year, month)
    last = get_last_day(first)
    return first, str(last)


def _get_slip_details(slip_names: list[str]) -> dict[str, dict[str, float]]:
    """Gom khoản cấu thành của mỗi phiếng lương: `{slip: {component: amount}}`.

    Vì sao gom thành dict thay vì để mỗi dòng gọi `get_value`: bản gốc gọi
    `_component_total()` **3 lần cho mỗi dòng** và `slip_name` lúc đó luôn
    `None`. Nay chỉ **một** truy vấn cho cả báo cáo.
    """
    out: dict[str, dict[str, float]] = {name: {} for name in slip_names}
    if not slip_names:
        return out

    rows = frappe.get_all(
        "Salary Detail",
        filters={"parent": ["in", slip_names], "parenttype": "Salary Slip"},
        fields=["parent", "salary_component", "amount"],
        limit_page_length=0,
    )
    for row in rows:
        bucket = out.get(row.parent)
        if bucket is None:
            continue
        component = row.salary_component
        bucket[component] = bucket.get(component, 0) + (row.amount or 0)
    return out


def _columns() -> list[dict]:
    return [
        {"label": _("Mã NV"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": _("Họ tên"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": _("Phòng ban"), "fieldname": "department", "fieldtype": "Data", "width": 140},
        {"label": _("Ngày công"), "fieldname": "payment_days", "fieldtype": "Float", "width": 90},
        {"label": _("Lương CB"), "fieldname": "basic_salary", "fieldtype": "Currency", "width": 120},
        {"label": _("Phụ cấp"), "fieldname": "allowances", "fieldtype": "Currency", "width": 120},
        {"label": _("Tổng thu nhập"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 130},
        {"label": _("BHXH NLĐ"), "fieldname": "bhxh", "fieldtype": "Currency", "width": 110},
        {"label": _("BHYT NLĐ"), "fieldname": "bhyt", "fieldtype": "Currency", "width": 110},
        {"label": _("BHTN NLĐ"), "fieldname": "bhtn", "fieldtype": "Currency", "width": 110},
        {"label": _("TN tính thuế"), "fieldname": "taxable_income", "fieldtype": "Currency", "width": 120},
        {"label": _("Thuế TNCN"), "fieldname": "pit", "fieldtype": "Currency", "width": 110},
        {"label": _("Thực lĩnh"), "fieldname": "net_pay", "fieldtype": "Currency", "width": 130},
    ]


def _get_data(filters: dict[str, Any]) -> list[dict]:
    conditions: dict[str, Any] = {"docstatus": 1}

    if filters.get("company"):
        conditions["company"] = filters["company"]
    if filters.get("department"):
        conditions["department"] = filters["department"]
    if filters.get("month") and filters.get("year"):
        conditions["start_date"] = ["between", _month_range(int(filters["year"]), int(filters["month"]))]

    # `base` đã bỏ: xem lý do (1) ở đầu file. Còn lại đều là cột có thật —
    # đã kiểm đủ 76 cột của `tabSalary Slip` trên staging.
    slips = frappe.get_all(
        "Salary Slip",
        filters=conditions,
        fields=[
            "name",
            "employee",
            "employee_name",
            "department",
            "payment_days",
            "gross_pay",
            "net_pay",
            "total_earnings",
            "vn_insurance_employee",
            "vn_pit_amount",
            "vn_taxable_income",
        ],
        order_by="department asc, employee_name asc",
        limit_page_length=0,
    )

    details = _get_slip_details([s.name for s in slips])
    basic_names = _basic_components()

    data: list[dict] = []
    for slip in slips:
        components = details.get(slip.name, {})

        basic = 0.0
        for name in basic_names:
            basic += components.get(name, 0)

        earnings = slip.total_earnings or 0
        # `max(0, …)` giữ nguyên phòng vệ của bản gốc: khi lương cơ bản lớn hơn
        # tổng thu nhập (cấu hình lương sai) thì báo cáo hiện 0 chứ không hiện
        # số âm trong bảng lương.
        allowances = max(0, earnings - basic)

        row = {
            "employee": slip.employee,
            "employee_name": slip.employee_name,
            "department": slip.department or "",
            "payment_days": slip.payment_days or 0,
            "basic_salary": basic,
            "allowances": allowances,
            "gross_pay": slip.gross_pay or 0,
            "taxable_income": slip.vn_taxable_income or 0,
            "pit": slip.vn_pit_amount or 0,
            "net_pay": slip.net_pay or 0,
        }
        for key, component in INSURANCE_COMPONENTS:
            row[key] = components.get(component, 0)
        data.append(row)

    return data


def execute(filters: dict | None = None) -> tuple[list[dict], list[dict]]:
    """Điểm vào của report. Giữ đúng chữ ký mà Frappe gọi."""
    filters = filters or {}
    return _columns(), _get_data(filters)