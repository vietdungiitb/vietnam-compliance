# HANDOFF — Chuẩn hoá tuân thủ kế toán VN cho `vietnam_compliance`

- **Ngày:** 26/11/2026
- **Repo:** `vietdungiitb/vietnam-compliance` — nhánh chính `main`
- **Trạng thái:** **DONE (pre-production)** — deploy staging PASS, không còn gate chờ người khác
- **PR đã merge:** #6 (fix P0 + S4 + owner decision), #7 (sửa field GL Entry), #8 (docs verify),
  #9 nếu có (handoff này). Merge cuối cùng `0733293`.

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

## 4. Còn lại / next steps (không chặn pre-production)

| Việc | Owner |
|---|---|
| Render PDF 8 mẫu + đối chiếu endpoint 5 T-VAN với tài liệu vendor | Ops/App khi có hợp đồng T-VAN |
| Chạy gates ERP-Edusuccess (`no-raw-sql`, `whitelist-methods`, …) nếu copy code sang | Tech lead ERP |
| O13: hook lương chỉ ghi 3 field, chưa đụng `total_deduction`/`net_pay` | App + ERP (backlog riêng) |
| TT 58/2026 (DN siêu nhỏ), BCTC TT 99, PIT lũy kế/quyết toán năm | App + KTT tương lai |
| Bật `VN E Invoice Settings.enabled` khi có hợp đồng T-VAN | Ops |

*Tài liệu này là bằng chứng theo `documentation-evidence-rule.md`. Không có hạng mục nào
bị bỏ lại dưới dạng "chờ KTT ký" theo chỉ thị owner 26/11/2026.*
