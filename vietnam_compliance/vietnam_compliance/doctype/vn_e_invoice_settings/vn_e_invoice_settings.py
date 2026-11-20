"""VN E Invoice Settings — Single DocType."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class VNEInvoiceSettings(Document):
    """Global settings for the Vietnamese e-invoicing integration.

    Selects one of the five supported providers and stores API /
    certificate credentials plus invoice-template metadata.
    """

    def validate(self) -> None:
        """Fail closed: enabling requires provider + T-VAN contract (NĐ 254/2026)."""
        if not self.enabled:
            return
        if not self.provider:
            frappe.throw(_("Cần chọn nhà cung cấp trước khi kích hoạt HĐĐT."))
        if self.invoice_type == "01GTKT" and not self.tvan_contract_no:
            frappe.throw(_("Cần số hợp đồng T-VAN theo NĐ 254/2026."))
