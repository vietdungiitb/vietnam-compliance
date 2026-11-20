# S-VN — vietnam-compliance: đóng F-06…F-10

> **Ngày:** 20/11/2026 · **Repo:** `vietdungiitb/vietnam-compliance` (clone freshest @ `11c05ab`)
> **Phạm vi:** 5 finding còn lại của audit tổng thể ERP-Edusuccess thuộc repo công ty.

## 1. Kết quả

| Finding | Trạng thái trước | Đã làm |
|---|---|---|
| F-06 e-invoice chưa enable | Settings schema có nhưng `provider` rỗng, hook im lặng, không có enable | Thêm `enabled` (mặc định 0), `invoice_type` (01GTKT/02GTTT), `tvan_contract_no` (NĐ 254/2026); controller validate fail-closed; dispatcher kiểm `enabled` trước gửi |
| F-07 KCT | Template hardcoded "không chịu thuế", mọi invoice đều in; không có flag | Thêm custom field `vn_is_kct` (Check) trên Sales Invoice; template điều kiện `doc.vn_is_kct or not doc.total_taxes_and_charges` → KCT note hoăc dòng thuế GTGT |
| F-08 CCCD | Không có field, không mã hoá, không mask | Thêm field `cccd` kiểu `Password` trên `VN Employee Tax Info`; util `payroll/cccd.py` (normalize/validate 12 số + prefix tỉnh, `mask_cccd` → `012****8901`) |
| F-09 CSS printview | Đã fix ở code (CSS nhúng vào 8 Print Format từ `a2b452a`), nhưng test nằm ngoài CI | CI giờ chạy `tests/ vietnam_compliance/tests/`; ruff check/compileall/validate-json trỏ đúng `vietnam_compliance/` (trước trỏ `erpnextvn/` không tồn tại) |
| F-10 default print format | Không có Property Setter, fresh site giữ ERPNext Classic | `print_format_defaults.py` upsert Property Setter `default_print_format` cho 4 DocType, chỉ khi country = Vietnam; gọi từ `after_install` |

## 2. Bằng chứng

```
python -m ruff check vietnam_compliance/          → All checks passed
python -m pytest vietnam_compliance/tests/ -q     → 14 passed, 8 subtests
python -m compileall -q vietnam_compliance/       → exit 0
```
14 test mới/cập nhật: `test_print_format_defaults` (3), `test_print_format_content` (+2 KCT), `test_einvoice_settings` (2), `test_cccd` (3).

## 3. Điều chỉnh CI

- `ruff check` bỏ `|| true` và trỏ đúng thư mục; sửa 6 lỗi pre-existing (`F841`, 5× `F403` trong shim proxy) để CI xanh thật.
- `ruff format --check` vẫn `|| true` — nợ format cũ của legacy report shims, ghi rõ comment.
- JSON validation + py_compile trỏ đúng `vietnam_compliance/`.

## 4. CHƯA XÁC MINH / CHƯA CHẠY

- Bench/site: `after_install` chạy Property Setter, render PDF có CSS/KCT, `frappe.get_single("VN E Invoice Settings").enabled` trên site thật — **CHƯA CHẠY** (không có site trong repo này).
- Endpoint API của 5 provider HĐĐT (Viettel/VNPT/MISA/FPT/BKAV) chưa đối chiếu tài liệu vendor — code cũ chỉ mang tính minh hoạ; **CHƯA XÁC MINH**.
- KTT (kế toán trưởng) cần ký bổ sung cho nội dung KCT theo commit `527bee1` — sandbox cho phép, production phải ký thật.
- `docs/COMPLIANCE-VN.md` (cites NĐ 13/2023) nằm ở repo ERP-Edusuccess — cross-repo handoff, không sửa ở đây.

*Tài liệu là bằng chứng theo `documentation-evidence-rule.md`.*
