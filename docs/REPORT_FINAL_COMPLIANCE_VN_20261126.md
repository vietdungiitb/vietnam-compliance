# REPORT FINAL — Đóng finding tuân thủ kế toán VN

> **Ngày:** 26/11/2026 · **Nhánh:** `fix/compliance-vn-20261126` · **Base:** `main @ cd2d7ec`
> **Auditor:** re-audit vòng 2 = **AGREE** (0 blocker, 0 major)

## 1. Phạm vi

Xử lý 6 finding P0 + các P1/P2 liên quan trực tiếp đến chuẩn mực kế toán VN trong app
`vietnam_compliance`, theo uỷ quyền "owner quyền cao nhất" của người dùng
(`docs/OWNER-DECISION-20261126.md`). Không sửa `smart_edu_core` (`AGENTS.md §2.2`).

## 2. Kết quả

| Việc | Trạng thái |
|---|---|
| P0-1 Ép `currency_precision = "0"` | Đã xoá (`setup.py:104-110`) |
| P0-2 Thuế TNCN 7 bậc → 5 bậc | Đã đổi + test 5 mức (`pit_calculator.py:37-44`) |
| P0-3 Trần BHXH 46,8tr → theo ngày 50,6tr | Đã đổi + `as_of` từ kỳ lương |
| P0-4 Lương tối thiểu NĐ 74 → NĐ 293/2025 | Đã đổi 4 vùng, có sàn, chặn vùng sai |
| P0-5 Không idempotency HĐĐT | Có `deduplication_id` unique + guard + không set "Đã phát hành" khi thiếu số HĐ |
| P0-6 Raw SQL f-string 4 report | Đổi sang `frappe.get_all` |
| P1 S2/S4/S5, company/overlap, KCT, print-format filter | Đã xử lý theo `PLAN` REQ-07..10 |

## 3. Bằng chứng chạy lệnh

```
(trước sửa) python -B -m pytest tests/test_compliance_2026.py -q → 26 failed, 2 passed
(sau sửa)   python -B -m pytest tests/ vietnam_compliance/tests/ -q → 25267 passed, 8 subtests
            python -m ruff check vietnam_compliance/ tests/       → All checks passed
            python -m compileall -q vietnam_compliance/ tests/    → exit 0
            JSON validate                                          → OK
            encoding: 25 file sửa, 0 ký tự U+FFFD
```

Diff: **20 file modified (+570 / −304)** + 5 file mới (`tests/test_compliance_2026.py`,
`PLAN`, `OWNER-DECISION`, `REPORT_FINAL`, `SUMMARY`).

## 4. Reservation / CHƯA CHẠY

1. **Ops:** `bench migrate` trên VPS staging (khoá `ENV-STAGING`), đếm log cũ before-add unique field.
2. **Ops:** cấp service account/API key riêng cho 6 chỗ `ignore_permissions=True` (R-OPS).
3. **Kế toán trưởng:** ký thật P0-2/3/4, P1-B3, nội dung KCT; đối chiếu văn bản gốc luật.
4. **CHƯA XÁC MINH:** `against_account` trong `GL Entry` (không có source ERPNext trong repo);
   hội tụ Property Setter thực tế; render PDF 8 mẫu; 5 provider T-VAN; gates ERP.
5. **Backlog riêng:** O13 (hook lương chỉ ghi 3 field, không đụng `total_deduction`/`net_pay`),
   TT 58/2026, cumulative PIT/quyết toán năm, BCTC theo TT 99, gỡ hook print-format trùng ở ERP.

## 5. Điều kiện lên production

Chưa đủ: phải hoàn thành mục 4.1–4.3. Uỷ quyền owner chỉ có hiệu lực development/sandbox.
