"""Vietnamese Personal Income Tax (PIT / Thuế TNCN) calculator.

Từ **kỳ tính thuế 2026**, Luật Thuế TNCN 109/2025/QH15 rút gọn từ 7 xuống
**5 bậc**. Dùng phương pháp giảm trừ nhanh (quick deduction).

Bảng bậc (thu nhập tính thuế/tháng, VND):

=====  ============  ======  =================
Stt    Upper limit   Rate    Quick deduction
=====  ============  ======  =================
1      10,000,000     5%     0
2      30,000,000    10%     500,000
3      60,000,000    20%     3,500,000
4     100,000,000    30%     9,500,000
5     > 100,000,000  35%     14,500,000
=====  ============  ======  =================

Giảm trừ nhanh được suy từ tính liên tục tại các ranh giới:
10tr×5% = 0,5tr; 30tr×20% − 3,5tr = 2,5tr (= 30tr×10% − 0,5tr); v.v.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple, Optional


class PITResult(NamedTuple):
    """Result of a PIT calculation."""

    taxable_income: float  # Thu nhập tính thuế
    tax_amount: float      # Số thuế TNCN
    effective_rate: float  # Thuế suất thực tế (%)
    bracket: int           # Bậc cao nhất áp dụng (1..5 theo Luật 109/2025)


#: ``(upper_limit, rate, quick_deduction)`` — 5 bậc theo Luật 109/2025/QH15.
TAX_BRACKETS: list[tuple[float, float, float]] = [
    (10_000_000,   0.05, 0),
    (30_000_000,   0.10, 500_000),
    (60_000_000,   0.20, 3_500_000),
    (100_000_000,  0.30, 9_500_000),
    (float("inf"), 0.35, 14_500_000),
]


def calculate_pit(
    gross_income: float,
    insurance_deduction: float,
    num_dependents: int = 0,
    personal_deduction: Optional[float] = None,
    dependent_deduction: Optional[float] = None,
    other_deductions: float = 0,
) -> PITResult:
    """Calculate the monthly Personal Income Tax (Thuế TNCN).

    Formula::

        Taxable = Gross
                − Insurance (employee)
                − Personal Deduction
                − (Dependents × Dependent Deduction)
                − Other Deductions

        Tax = Taxable × Rate − Quick Deduction

    Args:
        gross_income: Total gross salary (Tổng thu nhập chịu thuế).
        insurance_deduction: Employee BH contribution (BHXH + BHYT + BHTN).
        num_dependents: Number of registered dependents.
        personal_deduction: Override personal deduction.
            When ``None``, pulls ``VN Payroll Settings.personal_deduction``
            (default 15,500,000 VND per Resolution 110/2025/UBTVQH15,
            effective from tax year 2026).
        dependent_deduction: Override dependent deduction.
            When ``None``, pulls ``VN Payroll Settings.dependent_deduction``
            (default 6,200,000 VND per Resolution 110/2025/UBTVQH15,
            effective from tax year 2026).
        other_deductions: Any additional tax-deductible amounts.

    Returns:
        ``PITResult`` with ``taxable_income``, ``tax_amount``,
        ``effective_rate``, and ``bracket``.
    """
    if personal_deduction is None or dependent_deduction is None:
        personal_deduction, dependent_deduction = _resolve_deductions(
            personal_deduction, dependent_deduction
        )

    total_deductions = (
        insurance_deduction
        + personal_deduction
        + (num_dependents * dependent_deduction)
        + other_deductions
    )
    taxable_income = max(0.0, gross_income - total_deductions)

    if taxable_income == 0:
        return PITResult(0.0, 0.0, 0.0, 0)

    tax_amount = 0.0
    bracket = 0
    for i, (upper_limit, rate, quick_deduction) in enumerate(TAX_BRACKETS):
        if taxable_income <= upper_limit:
            tax_amount = taxable_income * rate - quick_deduction
            bracket = i + 1
            break

    # ROUND_HALF_UP theo tập quán kế toán VN (round() của Python là banker's rounding).
    tax_amount = float(
        max(
            Decimal("0"),
            Decimal(str(tax_amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP),
        )
    )
    effective_rate = (tax_amount / taxable_income * 100) if taxable_income else 0.0

    return PITResult(
        taxable_income=taxable_income,
        tax_amount=tax_amount,
        effective_rate=round(effective_rate, 2),
        bracket=bracket,
    )


def calculate_cumulative_withholding(
    monthly_taxable_incomes: list[float],
    num_dependents: int = 0,
    personal_deduction: float | None = None,
    dependent_deduction: float | None = None,
) -> list[float]:
    """Tính thuế khấu trừ từng tháng theo phương pháp **lũy kế**.

    Công thức: ``thuế tháng N = thuế(lũy kế đến N) − tổng thuế đã khấu trừ``.
    Khác với tính từng tháng độc lập: thu nhập không đều trong năm vẫn khớp
    biểu thuế lũy tiến của kỳ tính thuế (Luật 109/2025/QH15, NĐ 253/2026).

    Args:
        monthly_taxable_incomes: Thu nhập tính thuế của từng tháng (đã trừ BH).
        num_dependents: Số người phụ thuộc.
        personal_deduction / dependent_deduction: Override mức giảm trừ.

    Returns:
        Danh sách số thuế phải khấu trừ cho từng tháng.
    """
    if personal_deduction is None or dependent_deduction is None:
        personal_deduction, dependent_deduction = _resolve_deductions(
            personal_deduction, dependent_deduction
        )

    withheld = 0.0
    result: list[float] = []
    cumulative = 0.0
    for month_index, taxable in enumerate(monthly_taxable_incomes, start=1):
        cumulative += max(0.0, float(taxable))
        # Giảm trừ được cộng dồn theo SỐ THÁNG, không trừ mỗi tháng một lần
        # trên tổng thu nhập lũy kế.
        cumulative_tax = calculate_pit(
            cumulative,
            0,
            num_dependents=num_dependents,
            personal_deduction=(personal_deduction or 0) * month_index,
            dependent_deduction=(dependent_deduction or 0) * month_index,
        ).tax_amount
        monthly = max(0.0, cumulative_tax - withheld)
        result.append(monthly)
        withheld += monthly
    return result


def _resolve_deductions(
    personal: Optional[float], dependent: Optional[float]
) -> tuple[float, float]:
    """Resolve deduction values from ``VN Payroll Settings`` when not given.

    Falls back to the current statutory defaults if the settings doc or
    Frappe itself is unavailable (e.g. when running unit tests outside a
    bench).
    """
    # Statutory defaults per Resolution 110/2025/UBTVQH15 (effective 01/01/2026,
    # applies from tax year 2026).
    default_personal = 15_500_000.0
    default_dependent = 6_200_000.0

    try:
        import frappe

        settings = frappe.get_single("VN Payroll Settings")
        if personal is None:
            personal = settings.personal_deduction or default_personal
        if dependent is None:
            dependent = settings.dependent_deduction or default_dependent
    except Exception:
        if personal is None:
            personal = default_personal
        if dependent is None:
            dependent = default_dependent

    return float(personal), float(dependent)
