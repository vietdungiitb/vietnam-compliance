import json
import os
import pytest

def test_provinces_count_34():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "vietnam_compliance", "fixtures")
    provinces_file = os.path.join(fixtures_dir, "provinces.json")
    with open(provinces_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 34, f"Expected 34 provinces per NQ 202/2025/QH15, found {len(data)}"
    names = [p["name"] for p in data]
    assert "Hà Nội" in names
    assert "TP. Hồ Chí Minh" in names
    assert "Đà Nẵng" in names
    assert "Cần Thơ" in names
    assert "Hải Phòng" in names
    assert "Huế" in names
