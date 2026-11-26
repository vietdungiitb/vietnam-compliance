# PLAN — Đóng finding tuân thủ kế toán VN (26/11/2026)

> **Profile:** Generic (`workflow-dev-loop §2`) — repo không có gates/CLAIMS sẵn.
> **Quyền quyết:** người dùng là owner dự án, uỷ quyền quyền cao nhất và yêu cầu **tự quyết,
> không chờ kế toán trưởng**. Mọi mục thuế/BHXH/KCT được phê duyệt tại
> `docs/OWNER-DECISION-20261126.md` (mã `OWNER-APPROVED-20261126-*`) và áp dụng cho
> giai đoạn pre-production. Khi có KTT chính thức ở production, họ sẽ yêu cầu thay đổi
> nếu cần — đó là bước sau, không phải gate của phiên này.

## 1. Baseline đo được (lệnh tái tạo)

```
git rev-parse HEAD                     → cd2d7ec04269e507f0504e20d175dafcf43e8709
git rev-list --left-right --count origin/main...HEAD → 0 0
git status --short                     → (sạch trước khi tạo worktree)
python -B -m pytest vietnam_compliance/tests/ -q → 14 passed, 8 subtests
python -B -m pytest tests/ vietnam_compliance/tests/ -q → 25237 passed, 8 subtests
```

> Sửa theo objection O1 của auditor độc lập: `14 passed` chỉ đúng riêng
> `vietnam_compliance/tests/`; `tests/test_translations_csv.py` parametrize thêm 25.223 ca.

Ma trận nguồn pháp lý: `docs/AUDIT_TUAN-THU-KE-TOAN-VN_20261126.md` mục 2.

## 2. SCOPE / LIMIT / non-goals

**SCOPE (1 slice, tuần tự — các file chồng nhau):**
- `setup.py` (precision, province docstring, swallow exception)
- `accounting/tax_templates.py:81,99` (S4), `accounting/chart_of_accounts/__init__.py:41` (S5)
- `payroll/pit_calculator.py`, `payroll/insurance_calculator.py`, `payroll/utils.py`
  (`utils.py:176` phải truyền `as_of` lấy từ kỳ lương — objection O5)
- `e_invoicing/base_provider.py`, `e_invoicing/utils.py`, 5 provider,
  `doctype/vn_e_invoice_log/vn_e_invoice_log.json` (thêm `deduplication_id`)
- `vietnam_compliance/print_format_defaults.py`, mẫu `vn_hoa_don_ban_hang.json`
- 4 report raw SQL; `tests/**`; docs plan/claim/audit

**LIMIT:** tối đa 3 vòng sửa mỗi test; dừng và ghi blocker nếu vượt.

**Non-goals (có lý do, không phải quên):**
- TT 58/2026 (DN siêu nhỏ): nguồn có độ tin cậy trung bình, chưa có bản gốc ⇒ không thêm CoA
  mới, chỉ ghi backlog + cần đối chiếu bản gốc.
- Cumulative PIT / quyết toán năm (P1-B2): cần schema kỳ khai thuế & quyết định KTT về số kỳ ⇒
  ghi backlog, không giả định công thức.
- BCTC B01-DN/P&L (P1-A6): cần mẫu TT 99 chính thức + KTT chọn phương án ⇒ backlog.
- Mọi thứ cần site thật (mục 7 của audit) ⇒ `CHƯA CHẠY`, không tự báo PASS.
- Không sửa `smart_edu_core` (AGENTS.md §2.2 — tránh hai nguồn sự thật).

**Rollback:** xoá worktree + nhánh `fix/compliance-vn-20261126`; `main` không bị đụng.

## 3. Yêu cầu + tiêu chí nghiệm thu (Given/When/Then)

| REQ | Yêu cầu | AC |
|---|---|---|
| REQ-01 | Không ép precision/number_format toàn hệ thống | Given setup wizard chạy; When `setup_company_vietnam`; Then không gọi `set_single_value` cho 2 key đó |
| REQ-02 | PIT 5 bậc kỳ 2026 | Given TN tính thuế 20tr; When `calculate_pit`; Then 1.500.000đ (không phải 2.350.000đ); bậc 2; test ĐỎ trên code cũ |
| REQ-03 | Trần BHXH effective-dated | Given `as_of=2026-06-30` → 46,8tr; `2026-07-01` → 50,6tr; Given lương 0 → vẫn đóng theo sàn; **Given `payroll/utils.py:176` gọi hàm không truyền `as_of` ⇒ vẫn lấy ngày kỳ lương `start_date`, không rơi về mặc định** |
| REQ-04 | Lương tối thiểu NĐ 293/2025 | Given vùng I → 5,31tr; vùng IV → 3,70tr; region sai → throw |
| REQ-05 | Idempotency HĐĐT | Given cùng `deduplication_id` gọi 2 lần; Then 1 log, 1 lần gọi provider; HTTP 200 thiếu số HĐ → KHÔNG set "Đã phát hành". Thêm field `deduplication_id` vào `vn_e_invoice_log.json` ⇒ **cần `bench migrate` trên VPS staging, khoá dòng claim `ENV-STAGING`** |
| REQ-06 | S1: hết raw SQL f-string trong 4 report | Given grep `frappe.db.sql`/f-string SQL trong `report/**`; Then rỗng |
| REQ-07 | S2/S4/S5 | Given grep `frappe.db.commit()`/`@frappe.whitelist()` thiếu `methods`; Then rỗng. `ignore_permissions=True` đã bị **xoá hoàn toàn** khỏi `tax_templates.py` (đường tạo template do người dùng gọi). Các chỗ còn lại nằm trong hook hệ thống/endpoint đã kiểm `has_permission`: **thu hẹp AC** — code chỉ cần comment giải thích + audit log; **API key riêng/service account là hạng mục Ops, CHƯA CHẠY** (xử lý ở R-OPS, không chặn slice này) |
| REQ-08 | Report lọc company + kỳ overlap | Given `execute()` thiếu company; Then `frappe.throw`; kỳ dùng overlap `start <= to AND end >= from` |
| REQ-09 | KCT chỉ theo cờ `vn_is_kct` | Given HĐ không đào tạo nhưng thuế = 0; Then KHÔNG in ghi chú "dạy học không chịu thuế" |
| REQ-10 | Hai hook default print format **hội tụ về một bản ghi** | Given app và ERP cùng upsert; Then cùng filter `doctype_or_field="DocType"`, `field_name=""`, `property="default_print_format"` ⇒ cùng 1 Property Setter, giá trị idempotent. **Không sửa `smart_edu_core`** (non-goal); cross-repo handoff ghi rõ ERP hook được phép giữ vì cùng filter/cùng giá trị |

## 4. Ma trận REQ → task → test

```
REQ-01 → T1 setup.py           → tests/test_setup_no_precision.py
REQ-02 → T2 pit_calculator     → tests/test_pit_calculator.py (sửa + test mới)
REQ-03 → T3 insurance_calc     → tests/test_insurance_calculator.py (sửa + test mới)
REQ-04 → T3 insurance_calc     → tests/test_insurance_calculator.py
REQ-05 → T4 e_invoicing        → tests/test_einvoice_idempotency.py
REQ-06 → T5 reports            → tests/test_no_raw_sql_reports.py
REQ-07 → T6 S2/S4/S5           → tests/test_safety_rules.py
REQ-08 → T5 reports            → tests/test_report_filters.py
REQ-09 → T7 print format       → tests/test_print_format_content.py (sửa)
REQ-10 → T7 print format       → tests/test_print_format_defaults.py (sửa)
```

## 5. Auditor độc lập (B3)

Plan gửi auditor độc lập chỉ đọc; verdict cần `PASS`/`AGREE` mới vào B5/B6.
Đã đọc lessons: `10-frappe-dac-thu.md`, `35-ghep-roi-doc-cot-sai-chua-mo-file.md`
(và `31-khong-ep-lam-tron-tang-he-thong.md` làm tham chiếu cross-repo).
