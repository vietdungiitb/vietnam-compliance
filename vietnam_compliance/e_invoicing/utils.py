"""E-Invoice dispatcher utilities.

Provides:

- ``get_provider()`` — factory returning the configured provider instance
- ``on_sales_invoice_submit`` / ``on_sales_invoice_cancel`` — doc hooks
- ``poll_pending_invoices`` — hourly scheduler task
- ``send_einvoice`` / ``cancel_einvoice`` — whitelisted endpoints for the
  Sales Invoice "Phát hành HĐĐT" / "Hủy HĐĐT" buttons
"""

from __future__ import annotations

import importlib

import frappe
from frappe import _

from .base_provider import BaseEInvoiceProvider, EInvoiceError

_PROVIDER_MAP = {
    "Viettel": "vietnam_compliance.e_invoicing.viettel:ViettelProvider",
    "VNPT": "vietnam_compliance.e_invoicing.vnpt:VNPTProvider",
    "MISA": "vietnam_compliance.e_invoicing.misa:MISAProvider",
    "FPT": "vietnam_compliance.e_invoicing.fpt:FPTProvider",
    "BKAV": "vietnam_compliance.e_invoicing.bkav:BKAVProvider",
}


def get_provider() -> BaseEInvoiceProvider:
    """Return the configured provider instance.

    Raises:
        frappe.ValidationError: if no provider is configured.
    """
    settings = frappe.get_single("VN E Invoice Settings")
    path = _PROVIDER_MAP.get(settings.provider)
    if not path:
        frappe.throw(_("Chưa cấu hình nhà cung cấp hóa đơn điện tử"))

    module_path, class_name = path.split(":")
    module = importlib.import_module(module_path)
    provider_cls = getattr(module, class_name)
    return provider_cls()


# ---------------------------------------------------------------------------
# DocType hooks
# ---------------------------------------------------------------------------


def on_sales_invoice_submit(doc, method=None) -> None:
    """Auto-send e-invoice on Sales Invoice submit when configured."""
    settings = frappe.get_single("VN E Invoice Settings")
    # F-06: master switch — silent until explicitly enabled and configured.
    if not settings.enabled or not settings.provider or not settings.auto_send_on_submit:
        return

    country = frappe.get_cached_value("Company", doc.company, "country")
    if country != "Vietnam":
        return

    try:
        provider = get_provider()
        # Mỗi Sales Invoice chỉ phát hành 1 lần dù hook chạy lại / bấm lại nút.
        provider.create_and_send(
            doc.name, deduplication_id=f"{doc.name}:{settings.provider}"
        )
        frappe.msgprint(_("Đã phát hành hóa đơn điện tử thành công"), indicator="green")
    except EInvoiceError as exc:
        frappe.log_error(title=f"E-Invoice send error for {doc.name}", message=str(exc))
        frappe.msgprint(
            _("Lỗi phát hành HĐĐT: {0}. Bạn có thể phát hành thủ công sau.").format(str(exc)),
            indicator="orange",
        )


def on_sales_invoice_cancel(doc, method=None) -> None:
    """Warn the user when cancelling a Sales Invoice that has a live HĐĐT."""
    if doc.get("vn_einvoice_status") == "Đã phát hành" and doc.get("vn_einvoice_number"):
        frappe.msgprint(
            _(
                "Lưu ý: Hóa đơn điện tử {0} cần được hủy riêng trên hệ thống HĐĐT."
            ).format(doc.vn_einvoice_number),
            indicator="orange",
        )


def poll_pending_invoices() -> None:
    """Hourly scheduler: refresh status of ``Pending`` e-invoice logs."""
    pending = frappe.get_all(
        "VN E Invoice Log",
        filters={"status": "Pending"},
        fields=["name", "transaction_id", "sales_invoice", "invoice_number"],
        limit=50,
    )
    if not pending:
        return

    try:
        provider = get_provider()
    except Exception as exc:
        frappe.log_error(title="E-Invoice poll: no provider", message=str(exc))
        return

    for log in pending:
        try:
            result = provider.get_status(log.transaction_id)
        except Exception as exc:
            frappe.log_error(
                title=f"E-Invoice poll {log.name}", message=str(exc)
            )
            continue

        if result["status"] == "accepted":
            # `get_status` chỉ trả {status, message} — KHÔNG có số hóa đơn.
            # Không được gán "Đã phát hành" cho SI khi chưa có số (O10).
            invoice_number = result.get("invoice_number") or log.get("invoice_number")
            if not invoice_number:
                frappe.log_error(
                    title=f"E-Invoice poll {log.name}: accepted nhưng thiếu số HĐ",
                    message="Giữ trạng thái Pending cho tới khi có số hóa đơn từ T-VAN",
                )
                continue
            frappe.db.set_value(
                "VN E Invoice Log",
                log.name,
                {"status": "Accepted", "invoice_number": invoice_number},
            )
            frappe.db.set_value(
                "Sales Invoice",
                log.sales_invoice,
                {"vn_einvoice_status": "Đã phát hành", "vn_einvoice_number": invoice_number},
            )
        elif result["status"] == "rejected":
            frappe.db.set_value("VN E Invoice Log", log.name, "status", "Rejected")


# ---------------------------------------------------------------------------
# Whitelisted endpoints for client-side buttons
# ---------------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def send_einvoice(sales_invoice: str) -> dict:
    """Publish the e-invoice for a given Sales Invoice.

    Called from the "Phát hành HĐĐT" button on the Sales Invoice form.
    """
    if not frappe.has_permission("Sales Invoice", "write", doc=sales_invoice):
        frappe.throw(_("Bạn không có quyền phát hành hóa đơn này"))

    settings = frappe.get_single("VN E Invoice Settings")
    provider = get_provider()
    result = provider.create_and_send(
        sales_invoice, deduplication_id=f"{sales_invoice}:{settings.provider}"
    )
    return result


@frappe.whitelist(methods=["POST"])
def cancel_einvoice(sales_invoice: str, reason: str) -> dict:
    """Cancel the published e-invoice for a Sales Invoice."""
    if not frappe.has_permission("Sales Invoice", "write", doc=sales_invoice):
        frappe.throw(_("Bạn không có quyền hủy hóa đơn này"))

    invoice_number = frappe.db.get_value(
        "Sales Invoice", sales_invoice, "vn_einvoice_number"
    )
    if not invoice_number:
        frappe.throw(_("Hóa đơn chưa có số hóa đơn điện tử"))

    provider = get_provider()
    result = provider.cancel(invoice_number, reason)

    # HTTP 200 chưa chắc là hủy thành công: chỉ ghi "Đã hủy" khi provider xác nhận.
    if str(result.get("status", "")).lower() not in {"cancelled", "canceled", "huy"}:
        frappe.throw(_("T-VAN chưa xác nhận hủy hóa đơn — trạng thái không đổi"))

    frappe.db.set_value("Sales Invoice", sales_invoice, "vn_einvoice_status", "Đã hủy")
    frappe.get_doc(
        {
            "doctype": "VN E Invoice Log",
            "sales_invoice": sales_invoice,
            "provider": provider.provider_name,
            "status": "Cancelled",
            "invoice_number": invoice_number,
            "error_message": reason,
        }
    ).insert(ignore_permissions=True)
    # S4: endpoint đã kiểm has_permission("Sales Invoice","write") ở trên;
    # API key riêng: CHƯA CHẠY (Ops cấp service account — PLAN R-OPS);
    # audit log = Version/Error Log trên site.
    return result
