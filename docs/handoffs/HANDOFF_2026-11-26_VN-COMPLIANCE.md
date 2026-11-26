# HANDOFF — Chuẩn hoá tuân thủ kế toán VN cho `vietnam_compliance`

- **Ngày:** 26/11/2026
- **Repo:** `vietdungiitb/vietnam-compliance` — nhánh chính `main`
- **Trạng thái:** **DONE (pre-production)** — deploy staging PASS, không còn gate chờ người khác
- **PR đã merge:** #6 (fix P0 + S4 + owner decision), #7 (field GL Entry), #8 (docs verify),
  #9 (handoff), #10 (patch migrate custom field + bỏ thuế trùng), #11 (BCTC TT 99 + PIT lũy kế).
  Merge cuối cùng `b288d36`.

## 1. Phạm vi đã làm

- Đóng 6 finding P0 từ `docs/AUDIT_TUAN-THU-KE-TOAN-VN_20261126.md`.
- Đóng S4 bằng RBAC thật: bỏ `ignore_permissions=True`, cấp `create/write` trên
  `VN E Invoice Log` cho `Accounts User`/`Accounts Manager`.
- Owner tự phê duyệt mọi mục thuế/BHXH/KCT cho pre-production
  (`docs/OWNER-DECISION-20261126.md`) — **không chờ KTT**; KTT khi có ở production sẽ yêu cầu
  thay đổi nếu cần.
- Deploy staging + migrate + smoke test xong; claim `ENV-STAGING` đã mở và đóng đúng quy trình.

## 2. Bằng chứng (tự chạy lại được)

| Việc | Kết quả |
|---|---|
| Unit test | `python -B -m pytest tests/ vietnam_compliance/tests/ -q` → **25265 passed, 8 subtests** (sau PR #7: 31 test compliance xanh) |
| Lint/CI | `ruff.toml` khoá bộ rule `E4/E7/E9+F`; PR #6/#7/#8 CI **4/4 pass** |
| Re-audit | Auditor độc lập vòng 2: **AGREE**, 0 blocker/major |
| Deploy staging | `ops/scripts/deploy-staging.sh` **10/10 PASS**, SHA `27475edc` |
| Rebuild | `docker compose build --no-cache frappe-backend` — cần thiết vì Docker cache giữ app cũ |
| Migrate | `bench --site erp.edusuccess.vn migrate` PASS; `deduplication_id` = True trên schema |
| Công thức trên site | PIT 20tr → **1.500.000đ/bậc 2**; BHXH 30/06 → **3.744.000đ**, 01/07 → **4.048.000đ** |
| Báo cáo | TrialBalance 8/8, GeneralLedger 8/1, InvoiceRegister 10/2, PITReport 7/0 — OK |
| Site health | `check-site-health.sh` → **0 lỗi/24h**, VND baseline OK |
| Asset | `verify-assets.sh` → **164 mục, 0 lỗi** |

## 3. Lỗi phát hiện và đóng trong quá trình deploy

1. Docker build dùng layer cache ⇒ staging vẫn chạy app cũ — đã rebuild `--no-cache`.
2. `against_account` không tồn tại trong `GL Entry` (thực tế là `against`) — đã sửa PR #7 +
   test khoá field.
3. `ruff` trên runner dùng bộ rule lệch (41 lỗi legacy) — đã thêm `ruff.toml`.
4. Worktree `core.bare=true` làm gate `conflict-marker` tự kiểm đỏ — đã phục hồi bằng
   `ops/scripts/fix-worktree-config.mjs --recover` + `git config --worktree core.bare false`.

## 4. Đã đóng thêm trong phiên tiếp theo

| Việc | Bằng chứng trên staging |
|---|---|
| Patch migrate `v0_3` | `Custom Field` module VN **20 bản ghi** (trước = 0); `vn_is_kct` tồn tại |
| O13 thuế trùng | Salary Structure chỉ còn **1 component `Thuế TNCN`** (`Income Tax` đã bị patch xoá) |
| Render mẫu in | `frappe.get_print` → HTML 11.664 ký tự, CSS field 2.030 ký tự; cờ KCT hiện đúng, dòng thuế GTGT ẩn |
| BCTC TT 99 | `VN Bảng Cân Đối Kế Toán` OK 4/8, `VN Báo Cáo Kết Quả Kinh Doanh` OK 4/4 |
| PIT lũy kế | `calculate_cumulative_withholding([10tr, 30tr])` → `[500k, 4tr]` trên site; hook dùng dữ liệu các slip cùng năm |
| Site health | 0 lỗi/24h sau mỗi lần migrate |

## 5. Còn lại (không chặn pre-production)

| Việc | Owner |
|---|---|
| Đối chiếu endpoint 5 T-VAN với tài liệu vendor | Ops/App khi có hợp đồng T-VAN |
| Chạy gates ERP-Edusuccess nếu copy code sang | Tech lead ERP |
| TT 58/2026 (DN siêu nhỏ) — chờ bản gốc chính thức để làm CoA | App |
| Bật `VN E Invoice Settings.enabled` khi có hợp đồng T-VAN (hiện cố tình = 0, fail-closed) | Ops |

*Tài liệu này là bằng chứng theo `documentation-evidence-rule.md`. Không có hạng mục nào
bị bỏ lại dưới dạng "chờ KTT ký" theo chỉ thị owner 26/11/2026.*
