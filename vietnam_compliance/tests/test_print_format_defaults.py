"""F-10: Vietnamese print formats must become defaults after install."""

from __future__ import annotations

import sys
import types
from types import SimpleNamespace


def _stub_frappe(
    *, print_formats: set[str], existing_ps: set[str], country: str = "Vietnam"
):
    calls: list[tuple] = []
    mod = types.ModuleType("frappe")

    class DB:
        def exists(self, doctype, name, *a, **k):
            if doctype == "Print Format":
                return name in print_formats
            if doctype == "Property Setter":
                return name in existing_ps
            return None

        def get_value(self, doctype, name, field, *a, **k):
            if doctype == "Company" and field == "country":
                return country
            return None

        def set_value(self, doctype, name, field, value, *a, **k):
            calls.append((doctype, name, field, value))

    def get_doc(values):
        calls.append(("insert", values))
        return SimpleNamespace(insert=lambda **kw: None)

    mod.db = DB()
    mod.get_doc = get_doc
    saved = sys.modules.get("frappe")
    sys.modules["frappe"] = mod
    return saved, calls


def _restore(saved):
    if saved is not None:
        sys.modules["frappe"] = saved
    else:
        sys.modules.pop("frappe", None)


def test_sets_default_when_format_exists():
    from vietnam_compliance.vietnam_compliance.print_format_defaults import (
        set_default_print_formats,
    )

    saved, calls = _stub_frappe(
        print_formats={
            "VN Hóa Đơn Bán Hàng",
            "VN Phiếu Thu",
            "VN Hóa Đơn Mua Hàng",
            "VN Báo Giá",
        },
        existing_ps=set(),
    )
    try:
        result = set_default_print_formats("EDU")
    finally:
        _restore(saved)
    assert result["applied"] == [
        "Sales Invoice",
        "Payment Entry",
        "Purchase Invoice",
        "Quotation",
    ]
    assert any(
        c[0] == "insert" and c[1]["field_name"] == "default_print_format" for c in calls
    )


def test_skips_missing_format():
    from vietnam_compliance.vietnam_compliance.print_format_defaults import (
        set_default_print_formats,
    )

    saved, calls = _stub_frappe(print_formats=set(), existing_ps=set())
    try:
        result = set_default_print_formats()
    finally:
        _restore(saved)
    assert result["applied"] == []
    assert len(result["skipped"]) == 4
    assert not any(c[0] == "insert" for c in calls)


def test_non_vn_company_untouched():
    from vietnam_compliance.vietnam_compliance.print_format_defaults import (
        set_default_print_formats,
    )

    saved, calls = _stub_frappe(
        print_formats={"VN Hóa Đơn Bán Hàng"}, existing_ps=set(), country="US"
    )
    try:
        result = set_default_print_formats("US-CO")
    finally:
        _restore(saved)
    assert result["reason"] == "non-vn-company"
    assert not any(c[0] == "insert" for c in calls)
