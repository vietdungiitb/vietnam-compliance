"""Guard against a structurally broken ``vi.csv`` - each bad row silently logs errors.

**Why this test exists (measured 19/10/2026 on the ERP-Edusuccess staging site):**

Frappe loads translations through ``frappe/translate.py::get_translation_dict_from_file``,
and that function only accepts rows of exactly **2 or 3 columns**. Everything else falls
into this branch::

    elif item:
        msg = f"Bad translation in '{app}' for language '{lang}': {cstr(item)}"
        frappe.log_error(message=msg, title="Error in translation file")

So one malformed row produces one Error Log row on *every* translation sync (migrate,
build, language switch). The staging site had 6 malformed rows, which is where its
~690 errors over 2 days came from - all of them data defects, none of them code defects.

Two defects were present when this guard was written:

1. **Four sentences containing commas but without CSV escaping.** A row such as
   ``Due to stock closing entry {0}, you cannot repost item valuation before {1}``
   was parsed into 5 separate fields instead of 2.
2. **Two non-translation rows** left inside the translation table: a batch note
   (``# BATCH 18: Geography, Countries, Timezones, Regions``) and a number-format
   sample (``1234567.89,1.234.567,89,``).

The guard also checks for ``U+FFFD``: the Unicode replacement character is the
signature of Vietnamese text whose encoding broke - it has already happened here once
(``Xóa thẻ khỏi đã chọn`` had become ``Xóa th�� khỏi đã chọn``).

Run: ``python -m pytest tests/test_translations_csv.py -q``
"""

from __future__ import annotations

import csv
import pathlib
import re

import pytest

CSV_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "vietnam_compliance/translations/vi.csv"
)

#: ``frappe/translate.py`` accepts only 2- or 3-column rows - keep this in sync.
ACCEPTED_WIDTHS = (2, 3)

PLACEHOLDER = re.compile(r"\{(\d+)\}")


def _rows() -> list[list[str]]:
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


def test_translation_file_exists():
    """Without the file the whole app silently falls back to English."""
    assert CSV_PATH.is_file(), f"missing translation file: {CSV_PATH}"


def test_every_row_has_two_or_three_columns():
    """Contract with ``frappe/translate.py`` - breaking it logs an error on every sync."""
    offenders = [
        (index, row)
        for index, row in enumerate(_rows()[1:], start=2)
        if row and len(row) not in ACCEPTED_WIDTHS
    ]
    assert not offenders, (
        f"{len(offenders)} translation rows have an invalid column count (Frappe accepts 2 or 3). "
        f"First offender at line {offenders[0][0] if offenders else ''}: {offenders[0][1] if offenders else ''}\n"
        "Usual cause: a sentence with a comma inside that was never escaped. "
        'Fix by quoting the field: "source, with a comma","translation, with a comma"'
    )


def test_no_non_translation_rows():
    """Batch notes and number samples are not translations; they only produce errors.

    Only the two measured signatures are rejected. Broader rules delete real translations:
    several genuine ERPNext labels start with ``#`` (``# In Stock``, ``#{0}``).
    """
    rows = _rows()[1:]
    batch_markers = [
        (index, row[0][:60])
        for index, row in enumerate(rows, 2)
        if row and re.match(r"^#\s*BATCH\b", row[0])
    ]
    numeric_samples = [
        (index, row[:4])
        for index, row in enumerate(rows, 2)
        if row and re.fullmatch(r"[\d.,\s]+", row[0] or "")
    ]
    assert not batch_markers, (
        f"batch notes left inside the translation table: {batch_markers[:3]}"
    )
    assert not numeric_samples, (
        f"number-format samples are not translations: {numeric_samples[:3]}"
    )


def test_no_replacement_characters():
    """``U+FFFD`` means Vietnamese text was corrupted during editing."""
    text = CSV_PATH.read_text(encoding="utf-8")
    assert "\ufffd" not in text, (
        f"{text.count(chr(0xFFFD))} U+FFFD characters found - Vietnamese text is corrupted; "
        "restore the correct wording instead of dropping the row"
    )


@pytest.mark.parametrize(
    ("index", "row"),
    [
        (index, row)
        for index, row in enumerate(_rows()[1:], start=2)
        if len(row) == 3 and row[1]
    ],
    ids=lambda value: str(value)[:24],
)
def test_translation_keeps_placeholder_set(index: int, row: list[str]):
    """A ``{0}`` in the source must still exist in the translation, or the Desk shows ``{0}``."""
    source = set(PLACEHOLDER.findall(row[0]))
    target = set(PLACEHOLDER.findall(row[1]))
    assert source == target, (
        f"line {index}: source has {sorted(source)} but translation has {sorted(target)}"
    )
