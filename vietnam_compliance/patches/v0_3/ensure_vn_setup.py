"""Patch migrate: đảm bảo setup VN có hiệu lực trên site ĐÃ CÀI app từ bản cũ.

`after_install` chỉ chạy MỘT LẦN lúc cài app. Site nâng cấp từ bản trước không có
custom field `vn_is_kct`, `vn_einvoice_*`, `vn_insurance_*` ⇒ mẫu in KCT và hook
HĐĐT chết im lặng (đo staging 26/11/2026: `Custom Field` module VN = 0 bản ghi).

Patch này idempotent: chạy lại nhiều lần không tạo trùng.
"""

from __future__ import annotations

import frappe


def execute() -> None:
    from vietnam_compliance.vietnam_compliance.print_format_defaults import (
        set_default_print_formats,
    )
    from vietnam_compliance.vietnam_compliance.setup import (
        add_address_template,
        add_custom_fields,
        load_provinces,
    )

    add_custom_fields()
    load_provinces()
    add_address_template()
    set_default_print_formats()
    _dedupe_pit_component()


def _dedupe_pit_component() -> None:
    """Chỉ giữ một component thuế TNCN trên mỗi Salary Structure.

    Đo staging: structure "Giáo viên - Lương tối thiểu (G-703)" có cả
    `Income Tax` (IT) lẫn `Thuế TNCN` (TNCN) ⇒ lương thực lĩnh bị trừ thuế 2 lần.
    Giữ component VN (`Thuế TNCN`), bỏ component generic (`Income Tax`).
    """
    rows = frappe.get_all(
        "Salary Detail",
        filters={
            "parenttype": "Salary Structure",
            "salary_component": ("in", ["Income Tax", "Thuế TNCN"]),
        },
        fields=["name", "parent", "salary_component"],
    )
    by_parent: dict[str, set[str]] = {}
    for row in rows:
        by_parent.setdefault(row.parent, set()).add(row.salary_component)

    for parent, components in by_parent.items():
        if not {"Income Tax", "Thuế TNCN"}.issubset(components):
            continue
        for row in rows:
            if row.parent == parent and row.salary_component == "Income Tax":
                frappe.delete_doc("Salary Detail", row.name)
                frappe.logger().info(
                    f"Removed duplicate 'Income Tax' row from Salary Structure {parent}"
                )
