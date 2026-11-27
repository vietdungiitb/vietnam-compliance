"""Hợp đồng regional override: ERPNext v16 cần danh sách tên tài khoản.

Fail-before: `tax_templates.py` hiện trả dict ⇒ `push(...r.message)` ở client
(`taxes_and_totals.js:327`) nổ TypeError. File này chứng minh lỗi trước khi sửa.
"""

from __future__ import annotations

import sys
import types

# Module chạy unit không có frappe thật; stub đúng API duy nhất mà hàm dùng.
_fake_frappe = types.ModuleType("frappe")
_fake_frappe.get_cached_value = lambda doctype, name, field: {
    "abbr": "TECL",
    "cost_center": "Chi phí chung - TECL",
}.get(field)
sys.modules.setdefault("frappe", _fake_frappe)

from vietnam_compliance.accounting.tax_templates import get_round_off_accounts  # noqa: E402


def test_tra_ve_danh_sach_ten_tai_khoan():
    result = get_round_off_accounts("Công ty TECL")
    assert isinstance(result, list), f"phải là list, nhận {type(result).__name__}"
    assert len(result) == 1
    assert result[0] == "6428 - Chi phí bằng tiền khác - TECL"


def test_spread_duoc_nhuv_client_erpnext():
    flags: list[str] = []
    flags.extend(get_round_off_accounts("Công ty TECL"))
    assert flags == ["6428 - Chi phí bằng tiền khác - TECL"]
