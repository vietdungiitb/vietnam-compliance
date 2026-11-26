"""Finding tuân thủ 2026 — fail-before tests.

Mỗi test ĐỎ trên code cũ (cd2d7ec) và phải XANH sau khi sửa.
Chạy: python -B -m pytest tests/test_compliance_2026.py -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vietnam_compliance.payroll.insurance_calculator import (
    _DEFAULTS,
    calculate_insurance,
)
from vietnam_compliance.payroll.pit_calculator import TAX_BRACKETS, calculate_pit

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "vietnam_compliance"


def _read(rel: str) -> str:
    return (APP / rel).read_text(encoding="utf-8")


class TestPIT5Brackets2026:
    """Luật 109/2025/QH15: 5 bậc, giảm trừ nhanh 0/0,5/3,5/9,5/14,5tr."""

    def test_table_has_exactly_five_brackets(self):
        assert len(TAX_BRACKETS) == 5

    @pytest.mark.parametrize(
        ("taxable", "expected", "bracket"),
        [
            (4_000_000, 200_000, 1),
            (20_000_000, 1_500_000, 2),
            (50_000_000, 6_500_000, 3),
            (100_000_000, 20_500_000, 4),
            (101_000_000, 20_850_000, 5),
        ],
    )
    def test_tax_amount_per_new_bracket(self, taxable, expected, bracket):
        result = calculate_pit(
            taxable, 0, num_dependents=0,
            personal_deduction=0, dependent_deduction=0,
        )
        assert result.tax_amount == expected
        assert result.bracket == bracket

    def test_old_seven_bracket_table_is_gone(self):
        limits = [row[0] for row in TAX_BRACKETS]
        assert 5_000_000 not in limits
        assert 18_000_000 not in limits


class TestInsuranceEffectiveDated2026:
    def test_base_salary_is_2530000_default(self):
        assert _DEFAULTS["base_salary"] == 2_530_000.0

    def test_ceiling_switches_on_2026_07_01(self):
        before = calculate_insurance(60_000_000, "I", as_of="2026-06-30")
        after = calculate_insurance(60_000_000, "I", as_of="2026-07-01")
        assert before.si_employee == round(46_800_000 * 0.08)
        assert after.si_employee == round(50_600_000 * 0.08)
        assert after.si_employee > before.si_employee

    @pytest.mark.parametrize(
        ("region_index", "wage"),
        [("1", 5_310_000.0), ("2", 4_730_000.0),
         ("3", 4_140_000.0), ("4", 3_700_000.0)],
    )
    def test_min_wage_nd293(self, region_index, wage):
        assert _DEFAULTS[f"min_wage_region_{region_index}"] == wage

    def test_zero_salary_still_pays_floor(self):
        r = calculate_insurance(0, "I", as_of="2026-07-01")
        assert r.si_employee == round(2_530_000 * 0.08)
        assert r.total_employee > 0

    def test_invalid_region_does_not_silently_use_region_i(self):
        with pytest.raises((ValueError, Exception)) as exc:
            calculate_insurance(10_000_000, "Vùng 1", as_of="2026-07-01")
        assert "I" not in str(exc.value) or "vùng" in str(exc.value).lower()

    def _with_frappe_single(self, values: dict):
        """Stub `frappe.get_single` để kiểm chứng effective-date TRÊN SITE."""
        import sys
        import types
        from types import SimpleNamespace

        saved = sys.modules.get("frappe")
        module = types.ModuleType("frappe")

        class DB:
            @staticmethod
            def set_value(*args, **kwargs):
                return None

        module.db = DB()
        module.get_single = lambda doctype: SimpleNamespace(
            **{**{k: None for k in _DEFAULTS}, **values}
        )
        module.log_error = lambda **kwargs: None
        sys.modules["frappe"] = module
        return saved

    def test_site_defaults_do_not_kill_historical_effective_date(self):
        """O8: Single có default mới (2,53tr) nhưng kỳ 30/06/2026 vẫn dùng 46,8tr."""
        import sys

        saved = self._with_frappe_single({"base_salary": 2_530_000})
        try:
            r = calculate_insurance(60_000_000, "I", as_of="2026-06-30")
        finally:
            if saved is None:
                sys.modules.pop("frappe", None)
            else:
                sys.modules["frappe"] = saved
        assert r.si_employee == round(46_800_000 * 0.08)

    def test_explicit_settings_with_effective_date_are_respected(self):
        """O9: kế toán khai effective_date và mức cũ ⇒ ý định của họ được giữ."""
        import sys

        saved = self._with_frappe_single({
            "base_salary": 2_340_000, "effective_date": "2026-01-01",
        })
        try:
            r = calculate_insurance(60_000_000, "I", as_of="2026-07-01")
        finally:
            if saved is None:
                sys.modules.pop("frappe", None)
            else:
                sys.modules["frappe"] = saved
        assert r.si_employee == round(46_800_000 * 0.08)


class TestSetupDoesNotTouchGlobalPrecision:
    def test_no_precision_or_number_format_override(self):
        src = _read("vietnam_compliance/setup.py")
        assert '"currency_precision"' not in src
        assert '"number_format"' not in src

    def test_tax_template_failure_is_not_swallowed(self):
        src = _read("vietnam_compliance/setup.py")
        assert "create_tax_templates failed" not in src


class TestEInvoiceIdempotency:
    def test_log_schema_has_dedup_field(self):
        raw = (APP / "vietnam_compliance/doctype/vn_e_invoice_log/vn_e_invoice_log.json").read_text(
            encoding="utf-8"
        )
        data = json.loads(raw)
        fields = {f["fieldname"] for f in data["fields"]}
        assert "deduplication_id" in fields
        # S4: thay vì bypass RBAC, cấp quyền tường minh cho role nghiệp vụ.
        accounts = [p for p in data["permissions"] if p["role"] == "Accounts User"]
        assert accounts and accounts[0].get("create") == 1
        assert accounts[0].get("write") == 1

    def test_dispatchers_are_post_only(self):
        src = _read("e_invoicing/utils.py")
        assert src.count('@frappe.whitelist(methods=["POST"])') >= 2
        assert "@frappe.whitelist()" not in src

    def test_create_and_send_guards_duplicate_and_missing_number(self):
        src = _read("e_invoicing/base_provider.py")
        assert "deduplication_id" in src
        assert "invoice_number" in src.split("def create_and_send")[1].split("def _log_success")[0]


class TestSafetyRulesS1S2S4S5:
    def test_no_raw_sql_in_reports(self):
        for path in (APP / "vietnam_compliance/report").rglob("*.py"):
            src = path.read_text(encoding="utf-8")
            assert "frappe.db.sql" not in src, path.name
            assert "f\"\"\"" not in src, path.name

    def test_no_manual_commit_in_setup(self):
        # Chỉ soi dòng LỆNH, không soi comment giải thích tại sao không commit.
        executing_lines = [
            line for line in _read("vietnam_compliance/setup.py").splitlines()
            if line.strip().startswith("frappe.db.commit(")
        ]
        assert executing_lines == []

    def test_no_permission_bypass_anywhere(self):
        """S4: RBAC không bị bypass — quyền được cấp trong DocType JSON."""
        for path in APP.rglob("*.py"):
            src = path.read_text(encoding="utf-8")
            assert "ignore_permissions=True" not in src, path.name

    def test_no_whitelist_without_methods(self):
        for path in APP.rglob("*.py"):
            src = path.read_text(encoding="utf-8")
            assert "@frappe.whitelist()" not in src, path.name


class TestReportFilters:
    def test_migrate_patch_ensures_setup_on_existing_sites(self):
        """after_install không chạy khi nâng cấp site — bắt buộc có patch migrate."""
        patches = (APP / "patches.txt").read_text(encoding="utf-8")
        assert "vietnam_compliance.patches.v0_3.ensure_vn_setup" in patches
        patch_src = _read("patches/v0_3/ensure_vn_setup.py")
        assert "add_custom_fields()" in patch_src
        assert "Income Tax" in patch_src and "Thuế TNCN" in patch_src

    def test_so_cai_uses_real_gl_field(self):
        """Đo trên staging: GL Entry có `against`, KHÔNG có `against_account`."""
        src = _read("vietnam_compliance/report/vn_so_cai/vn_so_cai.py")
        assert '"against"' in src
        assert "entry.against_account" not in src

    def test_company_is_mandatory(self):
        for rel in (
            "vietnam_compliance/report/vn_so_cai/vn_so_cai.py",
            "vietnam_compliance/report/vn_bang_ke_hoa_don/vn_bang_ke_hoa_don.py",
            "vietnam_compliance/report/vn_bao_cao_thue_tncn/vn_bao_cao_thue_tncn.py",
        ):
            src = _read(rel)
            assert "if not company:" in src, rel

    def test_pit_report_uses_overlap_range(self):
        src = _read("vietnam_compliance/report/vn_bao_cao_thue_tncn/vn_bao_cao_thue_tncn.py")
        assert 'doc_filters["start_date"] = ("<=", to_date)' in src
        assert 'doc_filters["end_date"] = (">=", from_date)' in src


class TestPrintFormat2026:
    def test_kct_note_only_from_explicit_flag(self):
        raw = (APP / "vietnam_compliance/print_format/vn_hoa_don_ban_hang/vn_hoa_don_ban_hang.json").read_text(
            encoding="utf-8"
        )
        assert "doc.vn_is_kct or not doc.total_taxes_and_charges" not in raw
        assert "doc.vn_is_kct" in raw

    def test_default_property_setter_converges_with_erp_hook(self):
        src = _read("vietnam_compliance/print_format_defaults.py")
        assert '"doctype_or_field": "DocType"' in src
        assert '"field_name": ""' in src
