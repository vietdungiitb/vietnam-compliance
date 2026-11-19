"""Kiểm chứng CSS được nạp vào field `css` của 8 Print Format VN.

Phép thử ĐỎ: file JSON hiện chỉ có `html`, không có `css` ⇒ printview
không nạp được class `.vn-print/.doc-title/.bordered` dù file CSS có sẵn.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PF_DIR = REPO / "vietnam_compliance" / "vietnam_compliance" / "print_format"

FORMATS = (
    "vn_hoa_don_ban_hang",
    "vn_phieu_thu",
    "vn_phieu_chi",
    "vn_phieu_luong",
    "vn_bao_gia",
    "vn_don_mua_hang",
    "vn_phieu_nhap_kho",
    "vn_phieu_xuat_kho",
)

REQUIRED = (
    ".vn-print",
    ".vn-print .doc-title",
    ".vn-print table.bordered",
    ".vn-print .signatures .sig-block",
    "font-size: 18px",
)


class TestPrintFormatCssField(unittest.TestCase):
    def test_8_mau_deu_co_css(self) -> None:
        for name in FORMATS:
            path = PF_DIR / name / f"{name}.json"
            with self.subTest(format=name):
                data = json.loads(path.read_text(encoding="utf-8"))
                css = data.get("css", "")
                self.assertTrue(css, f"{name}: field 'css' rỗng")
                # Frappe migrate skip import khi modified cũ hơn bản trong DB.
                self.assertGreater(
                    data.get("modified", ""),
                    "2026-01-01",
                    f"{name}: modified quá cũ — migrate sẽ skip, css không vào DB",
                )
                for selector in REQUIRED:
                    self.assertIn(selector, css, f"{name}: thiếu {selector}")


if __name__ == "__main__":
    unittest.main()
