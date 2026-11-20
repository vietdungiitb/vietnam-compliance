"""CCCD handling for Vietnamese payroll (Luật 91/2025, NĐ 356/2025).

CCCD is personal data — store it only in `Password` (encrypted at rest) fields,
validate the 12-digit format + province prefix, and always mask in logs/UI.
No raw CCCD in info-level logs (ISO 27001 / OWASP).
"""

from __future__ import annotations

import re

#: First two digits of a valid Vietnamese CCCD province code.
VALID_PROVINCE_PREFIXES: frozenset[str] = frozenset(
    {
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
        "11", "12", "14", "15", "16", "17", "18", "19", "20", "21",
        "22", "23", "24", "25", "26", "27", "28", "29", "30", "31",
        "32", "33", "34", "35", "36", "37", "38", "39", "40", "41",
        "42", "43", "44", "45", "46", "47", "48", "49", "50", "51",
        "52", "53", "54", "55", "56", "57", "58", "59", "60", "61",
        "62", "63", "64", "65", "66", "67", "68", "69", "70", "71",
        "72", "73", "74", "75", "76", "77", "78", "79", "80", "81",
        "82", "83", "84", "85", "86", "87", "88", "89", "90", "91",
        "92", "93", "94", "95", "96",
    }
)


def normalize_cccd(value: object) -> str | None:
    """Strip spaces/dashes; return 12 digits or None (fail closed)."""
    if value is None:
        return None
    raw = re.sub(r"[\s\-]", "", str(value))
    return raw if raw.isdigit() and len(raw) == 12 else None


def is_valid_cccd(value: object) -> bool:
    """12 digits + known province prefix. Checksum variants are not assumed."""
    clean = normalize_cccd(value)
    return bool(clean and clean[:2] in VALID_PROVINCE_PREFIXES)


def mask_cccd(value: object) -> str:
    """Always mask before logging: 012345678901 -> 012****8901."""
    clean = normalize_cccd(value)
    if not clean:
        return "***"
    return f"{clean[:3]}****{clean[-4:]}"


__all__ = ["VALID_PROVINCE_PREFIXES", "is_valid_cccd", "mask_cccd", "normalize_cccd"]
