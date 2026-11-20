"""F-08: CCCD must be encrypted at rest and masked in logs (Luật 91/2025)."""

from __future__ import annotations

import json
from pathlib import Path

from vietnam_compliance.payroll.cccd import is_valid_cccd, mask_cccd, normalize_cccd

CFG = (
    Path(__file__).resolve().parents[1]
    / "vietnam_compliance"
    / "doctype"
    / "vn_employee_tax_info"
    / "vn_employee_tax_info.json"
)


def test_cccd_field_is_password():
    data = json.loads(CFG.read_text(encoding="utf-8"))
    field = next(f for f in data["fields"] if f["fieldname"] == "cccd")
    assert field["fieldtype"] == "Password"
    assert field["translatable"] == 0


def test_normalize_and_validate():
    assert normalize_cccd("012 345 678 901") == "012345678901"
    assert is_valid_cccd("012345678901")
    assert not is_valid_cccd("992345678901")  # invalid province prefix
    assert not is_valid_cccd("01234567890")  # 11 digits


def test_always_mask():
    assert mask_cccd("012345678901") == "012****8901"
    assert mask_cccd("bad") == "***"
    assert "12345678" not in mask_cccd("012345678901")
