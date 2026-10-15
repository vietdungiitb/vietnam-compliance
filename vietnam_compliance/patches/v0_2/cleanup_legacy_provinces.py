"""Dọn dẹp danh mục 63 tỉnh cũ để nạp danh mục 34 tỉnh mới chuẩn NQ 202/2025/QH15.

Khi nâng cấp từ bản cũ (63 tỉnh) lên bản mới (34 tỉnh), các mã tỉnh cũ (như '46' của Thừa Thiên Huế)
sẽ gây xung đột Duplicate key khi fixture nạp tên mới ('Huế'). Xóa sạch bảng VN Province ở bước patch
để fixtures/provinces.json tái tạo chuẩn xác 34 đơn vị hành chính.
"""

import frappe


def execute() -> None:
    """Xóa danh mục tỉnh cũ trước khi fixtures đồng bộ 34 tỉnh mới."""
    if frappe.db.exists("DocType", "VN Province"):
        frappe.db.delete("VN Province")
