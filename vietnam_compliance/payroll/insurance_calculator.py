"""Vietnamese social insurance calculator (BHXH / BHYT / BHTN / KPCĐ).

Thông số có **hiệu lực theo ngày** — không được hard-code một mức cho mọi kỳ:

- Mức tham chiếu (lương cơ sở): 2.340.000đ đến 30/06/2026 (NĐ 73/2024),
  **2.530.000đ từ 01/07/2026** (NĐ 161/2026) ⇒ trần BHXH/BHYT 46,8tr → 50,6tr.
- Lương tối thiểu vùng: NĐ 74/2024 đến hết 2025, **NĐ 293/2025 từ 01/01/2026**
  (5,31 / 4,73 / 4,14 / 3,70 triệu), NĐ 399/2026 từ 01/01/2027.
- Sàn đóng = mức tham chiếu (Luật BHXH 41/2024/QH15) — không được để 0.

Tỷ lệ hiện hành: NLĐ 8% + 1,5% + 1% = 10,5%; DN 17,5% + 3% + 1% = 21,5%;
KPCĐ 2% trên quỹ lương (truyền ``total_payroll``).

Giá trị từ ``VN Payroll Settings`` (nếu có) được ưu tiên hơn mặc định luật —
cho phép kế toán điều chỉnh có kiểm soát thay vì sửa code.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import NamedTuple, Optional


class InsuranceResult(NamedTuple):
    """Breakdown of insurance contributions."""

    # Employee-paid
    si_employee: float   # BHXH NLĐ
    hi_employee: float   # BHYT NLĐ
    ui_employee: float   # BHTN NLĐ
    total_employee: float

    # Employer-paid
    si_employer: float   # BHXH DN
    hi_employer: float   # BHYT DN
    ui_employer: float   # BHTN DN
    union_fee: float     # KPCĐ DN
    total_employer: float


#: Mặc định hiện hành (từ 01/07/2026 cho lương cơ sở, 01/01/2026 cho lương tối thiểu).
_DEFAULTS = {
    "base_salary": 2_530_000.0,
    "si_hi_ceiling_multiplier": 20,
    "ui_ceiling_multiplier": 20,
    "min_wage_region_1": 5_310_000.0,
    "min_wage_region_2": 4_730_000.0,
    "min_wage_region_3": 4_140_000.0,
    "min_wage_region_4": 3_700_000.0,
    "si_employee_rate": 8.0,
    "hi_employee_rate": 1.5,
    "ui_employee_rate": 1.0,
    "si_employer_rate": 17.5,
    "hi_employer_rate": 3.0,
    "ui_employer_rate": 1.0,
    "union_fee_rate": 2.0,
}

#: Giá trị cũ để tính đúng các kỳ trước mốc hiệu lực (không ép lịch sử theo luật mới).
_LEGACY = {
    "base_salary_before_2026_07": 2_340_000.0,
    "min_wage_before_2026_01": {
        "I": 4_960_000.0,
        "II": 4_410_000.0,
        "III": 3_860_000.0,
        "IV": 3_450_000.0,
    },
}

_VALID_REGIONS = {"I", "II", "III", "IV"}


def _as_date(value: str | date | datetime | None) -> date:
    """Chuyển `as_of` sang `date`; mặc định là hôm nay."""
    if value is None:
        return date.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _validate_region(wage_region: str) -> str:
    """Chặn vùng sai thay vì im lặng rơi về vùng I (trần cao nhất)."""
    region = str(wage_region or "").strip().upper()
    if region not in _VALID_REGIONS:
        message = f"Vùng lương không hợp lệ: {wage_region!r}. Chỉ chấp nhận I, II, III, IV"
        try:
            import frappe
            frappe.throw(message)
        except ImportError:
            raise ValueError(message) from None
    return region


def calculate_insurance(
    insurance_salary: float,
    wage_region: str = "I",
    total_payroll: Optional[float] = None,
    as_of: str | date | None = None,
) -> InsuranceResult:
    """Calculate social insurance contributions for one employee.

    Args:
        insurance_salary: Salary used as the insurance base (Mức lương đóng BH).
        wage_region: One of ``"I"``, ``"II"``, ``"III"``, ``"IV"``.
        total_payroll: Total company payroll for the period, base for KPCĐ.
        as_of: Ngày tính lương — quyết định mức tham chiếu/lương tối thiểu áp dụng.

    Returns:
        ``InsuranceResult`` with rounded-to-integer VND amounts.
    """
    region = _validate_region(wage_region)
    settings = _resolve_settings(_as_date(as_of))

    base_salary = settings["base_salary"]
    si_hi_ceiling = settings["si_hi_ceiling_multiplier"] * base_salary

    min_wage_map = {
        "I": settings["min_wage_region_1"],
        "II": settings["min_wage_region_2"],
        "III": settings["min_wage_region_3"],
        "IV": settings["min_wage_region_4"],
    }
    min_wage = min_wage_map[region]
    ui_ceiling = settings["ui_ceiling_multiplier"] * min_wage

    # Sàn = mức tham chiếu; trần = 20 lần. Không được đóng 0 khi thiếu dữ liệu lương.
    base = max(base_salary, min(float(insurance_salary or 0), si_hi_ceiling))
    # BHTN có trần RIÊNG theo lương tối thiểu vùng (20 lần) — không lấy base
    # đã bị trần BHXH/BHYT giới hạn, nếu không vùng I/IV bị cùng một mức.
    ui_base = max(min_wage, min(float(insurance_salary or 0), ui_ceiling))

    si_employee = round(base * settings["si_employee_rate"] / 100)
    hi_employee = round(base * settings["hi_employee_rate"] / 100)
    ui_employee = round(ui_base * settings["ui_employee_rate"] / 100)
    total_employee = si_employee + hi_employee + ui_employee

    si_employer = round(base * settings["si_employer_rate"] / 100)
    hi_employer = round(base * settings["hi_employer_rate"] / 100)
    ui_employer = round(ui_base * settings["ui_employer_rate"] / 100)

    union_base = total_payroll if total_payroll is not None else insurance_salary
    union_fee = round((union_base or 0) * settings["union_fee_rate"] / 100)

    total_employer = si_employer + hi_employer + ui_employer + union_fee

    return InsuranceResult(
        si_employee=si_employee,
        hi_employee=hi_employee,
        ui_employee=ui_employee,
        total_employee=total_employee,
        si_employer=si_employer,
        hi_employer=hi_employer,
        ui_employer=ui_employer,
        union_fee=union_fee,
        total_employer=total_employer,
    )


#: Các khóa có mức luật thay đổi theo ngày — không được lấy từ Single một cách mù quáng.
_EFFECTIVE_DATED_KEYS = {
    "base_salary",
    "min_wage_region_1", "min_wage_region_2",
    "min_wage_region_3", "min_wage_region_4",
}


def _resolve_settings(as_of: date) -> dict:
    """Mặc định **theo ngày** + overlay cấu hình có `effective_date`.

    Quy tắc (đóng O8/O9 của re-audit):
    - Không đoán ý định kế toán bằng giá trị (`_is_stale_default` đã bị bỏ).
    - Nếu `VN Payroll Settings.effective_date` được khai và `as_of >= effective_date`
      ⇒ mọi giá trị do kế toán đặt có hiệu lực (kể cả mức "cũ" họ chủ ý dùng).
    - Nếu không khai `effective_date` ⇒ chỉ các khóa KHÔNG effective-dated
      (tỷ lệ, hệ số) được overlay; mức lương luật theo `as_of` được giữ nguyên.
    """
    settings = dict(_DEFAULTS)
    if as_of < date(2026, 7, 1):
        settings["base_salary"] = _LEGACY["base_salary_before_2026_07"]
    if as_of < date(2026, 1, 1):
        legacy = _LEGACY["min_wage_before_2026_01"]
        for region, value in legacy.items():
            settings[f"min_wage_region_{region}"] = value

    configured, effective_date = _load_settings()
    if effective_date is not None and as_of >= effective_date:
        for key, value in configured.items():
            if value is not None:
                settings[key] = value
    else:
        for key, value in configured.items():
            if value is not None and key not in _EFFECTIVE_DATED_KEYS:
                settings[key] = value
    return settings


def _load_settings() -> tuple[dict, date | None]:
    """Read ``VN Payroll Settings`` — trả (giá trị, ngày hiệu lực cấu hình)."""
    configured: dict = {key: None for key in _DEFAULTS}
    effective_date: date | None = None
    try:
        import frappe

        doc = frappe.get_single("VN Payroll Settings")
        for key in configured:
            value = getattr(doc, key, None)
            # Phân biệt 0 (admin cố tình đặt) với None (không đặt).
            if value is not None:
                configured[key] = float(value)
        raw_date = getattr(doc, "effective_date", None)
        if raw_date:
            effective_date = _as_date(str(raw_date))
    except Exception as exc:
        # Không nuốt im lặng: fallback ra luật nhưng để lại vết kiểm toán.
        try:
            import frappe
            frappe.log_error(
                title="VN Payroll Settings unavailable — dùng mặc định luật",
                message=str(exc),
            )
        except Exception:
            pass
    return configured, effective_date
