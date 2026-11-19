"""Kiểm chứng nội dung template VN theo plan T4/T6/T10 (chỉ đọc JSON)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

PF = Path(__file__).resolve().parents[1] / "vietnam_compliance" / "print_format"


def html_of(name: str) -> str:
    return json.loads((PF / name / f"{name}.json").read_text(encoding="utf-8"))["html"]


class TestTemplateContent(unittest.TestCase):
    def test_hoa_don_khong_chiu_thue(self) -> None:
        html = html_of("vn_hoa_don_ban_hang")
        self.assertIn("không chịu thuế GTGT", html)
        self.assertNotIn("Tiền thuế GTGT:", html)
        self.assertIn("so_tien_bang_chu(doc.rounded_total or doc.grand_total)", html)

    def test_hoa_don_co_qr_tuy_chon(self) -> None:
        html = html_of("vn_hoa_don_ban_hang")
        self.assertIn("invoice_qr_data_uri_optional(doc.name)", html)
        self.assertIn("Quét VietQR để thanh toán đúng số tiền", html)

    def test_phieu_thu_khong_lo_ghi_chu_noi_bo(self) -> None:
        html = html_of("vn_phieu_thu")
        self.assertIn("edu_payment_reason", html)
        self.assertNotIn("doc.remarks", html)


if __name__ == "__main__":
    unittest.main()
