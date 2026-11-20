"""F-06: e-invoice must have an explicit enable switch + NĐ 254/2026 fields."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = (
    ROOT
    / "vietnam_compliance"
    / "doctype"
    / "vn_e_invoice_settings"
    / "vn_e_invoice_settings.json"
)


def test_settings_have_enable_and_nd254_fields():
    data = json.loads(CFG.read_text(encoding="utf-8"))
    fields = {f["fieldname"]: f for f in data["fields"]}
    assert "enabled" in fields
    assert fields["enabled"]["default"] == "0"
    assert "invoice_type" in fields
    assert "02GTTT" in fields["invoice_type"]["options"]
    assert "tvan_contract_no" in fields


def test_submit_hook_checks_enabled():
    src = (ROOT / "e_invoicing" / "utils.py").read_text(encoding="utf-8")
    assert "if not settings.enabled or not settings.provider" in src
