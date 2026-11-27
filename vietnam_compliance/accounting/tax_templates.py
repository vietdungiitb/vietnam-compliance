"""Vietnam VAT tax template setup.

Creates Sales/Purchase tax templates for the standard Vietnamese VAT rates:
0% (export), 5% (essentials), 8% (reduced per NQ), 10% (standard).

Also provides the ``get_round_off_accounts`` regional override which maps
to account 6428 (Other miscellaneous expenses). The account numbers
``33311``, ``1331``, and ``6428`` are shared by TT200 and TT99/2025, so
this module works for both chart-of-accounts variants.
"""

from __future__ import annotations

import frappe


VAT_RATES = [
    {
        "title": "VAT Không chịu thuế - Dạy học, Dạy nghề",
        "rate": 0,
        "description": "Đối tượng không chịu thuế GTGT theo khoản 13 Điều 5 Luật Thuế GTGT 48/2024/QH15",
    },
    {
        "title": "VAT 0% - Xuất khẩu",
        "rate": 0,
        "description": "Thuế suất 0% cho hàng xuất khẩu",
    },
    {
        "title": "VAT 5% - Thiết yếu",
        "rate": 5,
        "description": "Thuế suất 5% cho hàng thiết yếu",
    },
    {
        "title": "VAT 8% - Giảm thuế",
        "rate": 8,
        "description": "Thuế suất 8% theo Nghị quyết giảm thuế",
    },
    {
        "title": "VAT 10% - Phổ thông",
        "rate": 10,
        "description": "Thuế suất phổ thông 10%",
    },
]


def create_tax_templates(company: str) -> None:
    """Create Vietnam VAT tax templates for a company.

    Args:
        company: Company name (Frappe primary key).
    """
    abbr = frappe.get_cached_value("Company", company, "abbr")

    # Default account heads (assumes TT200 CoA is already loaded).
    sales_tax_account = f"33311 - Thuế GTGT đầu ra - {abbr}"
    purchase_tax_account = f"1331 - Thuế GTGT được khấu trừ của hàng hóa, dịch vụ - {abbr}"

    # Fall back to any VAT-looking account if the exact name is missing.
    if not frappe.db.exists("Account", sales_tax_account):
        sales_tax_account = _find_account(company, ["3331", "33311"])
    if not frappe.db.exists("Account", purchase_tax_account):
        purchase_tax_account = _find_account(company, ["1331", "133"])

    if not sales_tax_account or not purchase_tax_account:
        # Không tạo template với account_head rỗng — hóa đơn sẽ không phải HĐĐT
        # đúng quy định và báo cáo thuế lệch. Dừng để kế toán cấu hình CoA.
        frappe.throw(
            "Thiếu tài khoản thuế GTGT (33311/1331). Vui lòng nạp hệ thống tài khoản trước."
        )

    for vat in VAT_RATES:
        # Kiểm theo (title, company) — autoname không đảm bảo "<title> - <abbr>".
        if not frappe.db.exists(
            "Sales Taxes and Charges Template",
            {"title": vat["title"], "company": company},
        ):
            frappe.get_doc(
                {
                    "doctype": "Sales Taxes and Charges Template",
                    "title": vat["title"],
                    "company": company,
                    "taxes": [
                        {
                            "charge_type": "On Net Total",
                            "account_head": sales_tax_account,
                            "description": vat["description"],
                            "rate": vat["rate"],
                        }
                    ],
                }
            ).insert()

        if not frappe.db.exists(
            "Purchase Taxes and Charges Template",
            {"title": vat["title"], "company": company},
        ):
            frappe.get_doc(
                {
                    "doctype": "Purchase Taxes and Charges Template",
                    "title": vat["title"],
                    "company": company,
                    "taxes": [
                        {
                            "charge_type": "On Net Total",
                            "account_head": purchase_tax_account,
                            "description": vat["description"],
                            "rate": vat["rate"],
                        }
                    ],
                }
            ).insert()


def _find_account(company: str, account_number_prefixes: list[str]) -> str | None:
    """Best-effort lookup of an account by number prefix."""
    for prefix in account_number_prefixes:
        name = frappe.db.get_value(
            "Account",
            {"company": company, "account_number": prefix, "is_group": 0},
            "name",
        )
        if name:
            return name
    return None


def get_round_off_accounts(company: str, account_list=None, doc=None) -> list[str]:
    """Trả về DANH SÁCH tài khoản làm tròn cho Việt Nam.

    Regional override cho ``erpnext.controllers.taxes_and_totals``. Phải trả
    `list[str]` vì ERPNext v16 dùng kết quả này ở cả server (`in`,
    `taxes_and_totals.py:843,855`) lẫn client (`push(...r.message)` rồi
    `.includes()` tại `taxes_and_totals.js:327,755,769`). Bản cũ trả `dict`
    ⇒ client nổ `TypeError: Spread syntax requires ...iterable`.
    """
    abbr = frappe.get_cached_value("Company", company, "abbr")
    return [f"6428 - Chi phí bằng tiền khác - {abbr}"]
