# SUMMARY — tuân thủ kế toán VN trong `vietnam_compliance`

**Ngày:** 26/11/2026 · **Nhánh:** `fix/compliance-vn-20261126` · **Verdict:** AGREE

## Đã làm

- Sửa toàn bộ 6 finding P0 của audit `docs/AUDIT_TUAN-THU-KE-TOAN-VN_20261126.md`.
- Đổi các thông số luật cũ sang hiệu lực 2026: biểu thuế 5 bậc, trần BHXH 50,6tr,
  lương tối thiểu NĐ 293/2025 — tất cả **effective-dated**, không hard-code một mức cho mọi kỳ.
- Bỏ ép `currency_precision = "0"` (lỗi làm tròn tiền thật đã từng phải khôi phục bằng binlog).
- Thêm idempotency phát hành HĐĐT (`deduplication_id` unique + guard + xác nhận số HĐ).
- Hết raw SQL trong 4 báo cáo; chặn thiếu `company`; kỳ thuế dùng độ phủ giao kỳ.
- Ghi chú "không chịu thuế" chỉ theo cờ `vn_is_kct`, không suy từ thuế = 0.
- 30 test mới trong `tests/test_compliance_2026.py` (28 ban đầu + 2 test effective-date có stub site).

## Test/gate

25267 passed, 8 subtests · ruff clean · compileall exit 0 · JSON OK · encoding sạch.
Auditor độc lập tự chạy lại và cho **AGREE**, không blocker/major.

## Chưa xong (không báo PASS)

`bench migrate` staging · service account cho S4 · KTT ký · xác minh `against_account`,
render PDF, 5 T-VAN, gates ERP · backlog O13/TT58/BCTC/PIT lũy kế.

## File chính

- Bằng chứng: `docs/AUDIT_TUAN-THU-KE-TOAN-VN_20261126.md` (mục 11)
- Kế hoạch/AC: `docs/PLAN_COMPLIANCE_VN_20261126.md`
- Quyết định owner: `docs/OWNER-DECISION-20261126.md`
- Báo cáo cuối: `docs/REPORT_FINAL_COMPLIANCE_VN_20261126.md`
