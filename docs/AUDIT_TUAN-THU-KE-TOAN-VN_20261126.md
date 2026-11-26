# AUDIT — Rà soát tuân thủ kế toán tài chính Việt Nam cho `vietnam_compliance`

> **Ngày:** 26/11/2026 · **Repo audit:** `vietdungiitb/vietnam-compliance` (clone local) ·
> **HEAD:** `cd2d7ec04269e507f0504e20d175dafcf43e8709` (branch `main`, `git status` sạch,
> `git rev-list --left-right --count origin/main...HEAD` = `0 0`) ·
> **Repo tiêu dùng:** ERP-Edusuccess (`origin/dev` đã fetch; working tree local đang lùi 63 commit
> nên KHÔNG ghi tài liệu vào checkout đó — bài học 93).

## 0. Phạm vi, phương pháp, giới hạn

- **Đối tượng:** toàn bộ app — `accounting/` (CoA TT200/TT133/TT99, tax template, regional
  override), `payroll/` (PIT, BHXH/BHYT/BHTN, CCCD), `e_invoicing/` (5 provider + hook + poll),
  5 báo cáo, 8 print format, fixture, `setup.py`, `hooks.py`.
- **Phương pháp:** 4 luồng audit độc lập **chỉ đọc** + 1 luồng tra cứu baseline pháp lý từ nguồn
  `.gov.vn`. Mọi finding có `path:line` đọc bằng read tool; không trích từ grep thuần (bài học 35).
- **Đã chạy:** `python -B -m pytest vietnam_compliance/tests/ -q` → **14 passed, 8 subtests**
  (test thuần Python, không cần site); `git status --short` vẫn rỗng sau chạy.
- **KHÔNG chạy:** test cần site, `bench migrate`, render PDF thật, truy vấn stub/staging —
  theo `AGENTS.md §7.1` (ERP-Edusuccess) mọi thử nghiệm có site chạy trên VPS staging, không chạy
  local Docker. Các mục đó ghi `CHƯA XÁC MINH`, không suy ra PASS.
- **Tài liệu này KHÔNG thay thế ý kiến của kế toán trưởng/luật sư thuế.** Mọi thay đổi thuế phải
  có chữ ký (`AGENTS.md §4`, `docs/COMPLIANCE-VN.md:3-6`).

## 1. Kết luận điều hành

**Chưa đạt "tương thích hoàn toàn chuẩn mực kế toán Việt Nam".** App có nền tảng tốt (CoA 3 bộ,
5 provider HĐĐT, 8 mẫu in, PIT/BHXH calculator) nhưng có **6 lỗi P0** — 4 lỗi do dùng thông số
pháp lý đã hết hiệu lực/hết hạn, 1 lỗi làm tròn tầng hệ thống, 1 lỗi idempotency phát hành hóa đơn.

| Nhóm | P0 | P1 | P2 | Đánh giá |
|---|---|---|---|---|
| Kế toán / báo cáo | 1 | 6 | 5 | Cấu trúc CoA tốt; thiếu BCTC, raw SQL, lọc company chưa chặt |
| Lương / thuế / BHXH | 3 | 4 | 5 | **Rủi ro tiền lương thật cao nhất** (thông số 2024–2025 cho kỳ 2026) |
| HĐĐT / mẫu in | 1 | 5 | 8 | Đã đóng F-06..F-10, nhưng chưa có dedup, chưa xử lý lỗi nghiệp vụ T-VAN |
| Cross-repo | 1 | 1 | 1 | Hai nguồn sự thật cho default print format + cấu hình tiền tệ |

**Khuyến nghị:** khóa 4 mốc effective-dated thay vì hard-code — `01/01/2026` (TT 99, NĐ 293,
giảm trừ TNCN, NQ 43), `01/07/2026` (NĐ 254/TT 91, Luật 109, NĐ 253, NĐ 161, TT 58),
`31/12/2026` (hết giảm GTGT 8%), `01/01/2027` (NĐ 399/2026 + luật miễn TNDN thông qua 20/11/2026,
chưa xác minh số hiệu).

---

## 2. Baseline pháp lý đối chiếu (đã tra cứu 26/11/2026)

| Nhóm | Văn bản | Hiệu lực | Yêu cầu chính | Nguồn |
|---|---|---|---|---|
| Chế độ kế toán | **TT 99/2025/TT-BTC** (27/10/2025) | 01/01/2026, năm TC bắt đầu từ/sau mốc này | Thay TT 200/2014, 75/2015, 53/2016, 195/2012; đổi BCTC mẫu B01-DN | [Bộ Tài chính](https://www.mof.gov.vn/tin-tuc-tai-chinh/tin-chinh-sach-tai-chinh/quy-dinh-moi-ve-che-do-ke-toan-doanh-nghiep) |
| Chế độ kế toán | TT 200/2014/TT-BTC | **Hết hiệu lực 01/01/2026** | Bị TT 99 thay thế (trừ khoản 2 Điều 31) | [Thư viện pháp luật](https://thuvienphapluat.vn/ma-so-thue/phap-luat-thue/thong-tu-2002014ttbtc-het-hieu-luc-tu-khi-nao-va-duoc-thay-the-boi-van-ban-nao-213871.html) |
| Chế độ kế toán | TT 133/2016/TT-BTC | Còn hiệu lực đến 11/2026 | DNNVV tiếp tục áp dụng hoặc tự nguyện sang TT 99; dự thảo thay thế lấy ý kiến 02/10/2026 — **CHƯA XÁC MINH** số hiệu ban hành | [Thư viện pháp luật](https://thuvienphapluat.vn/hoi-dap-phap-luat/nam-2026-co-con-ap-dung-thong-tu-133-doanh-nghiep-vua-va-nho-138106134.html) |
| Chế độ kế toán | **TT 58/2026/TT-BTC** (25/05/2026) | 01/07/2026 | DN siêu nhỏ: ghi sổ đơn dòng, không bắt buộc định khoản Nợ/Có — **cần đối chiếu bản gốc** (mức tin cậy trung bình) | [MAN](https://ketoan.man.net.vn/che-do-ke-toan-doanh-nghiep-sieu-nho) |
| Luật Kế toán | **Luật 56/2024/QH15** (29/11/2024) | 01/01/2025 (vài khoản 01/01/2026) | Bộ TC quy định chuẩn mực kế toán, chuẩn mực đạo đức nghề nghiệp | [Văn bản Chính phủ](https://vanban.chinhphu.vn?pageid=27160&docid=212484) |
| GTGT | Luật 48/2024/QH15, khoản 13 Điều 5 + NĐ 181/2025, khoản 7 Điều 4 | 01/07/2025 | Dạy học/dạy nghề theo pháp luật giáo dục = **không chịu thuế** (≠ miễn thuế) | [Lao động](https://laodong.vn/kinh-doanh/lam-ro-quy-dinh-thue-gtgt-va-uu-dai-thue-tndn-10-doi-voi-hoat-dong-dao-tao-day-nghe-1579654.ldo) |
| GTGT | NQ 204/2025 + NĐ 174/2025 | 01/07/2025 → **hết 31/12/2026** | Giảm 10% → 8%; ghi rõ "8%" trên HĐ; không áp cho đối tượng không chịu thuế/5% | [Chính phủ](https://baochinhphu.vn/giam-thue-gia-tri-gia-tang-tu-01-7-2025-den-het-31-12-2026-10225070118590677.htm) |
| TNDN | Luật 67/2025/QH15, Đ12(2)r + Đ13(2)b | 01/10/2025, kỳ 2025 | Ưu đãi 10% cho xã hội hóa giáo dục–đào tạo **theo danh mục/tiêu chí Thủ tướng**; hạch toán riêng hoạt động thương mại | [Công báo](https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2025/6/45557/57755-1-2025965-96667-2025-qh15.pdf) |
| TNDN | NQ 43/2026/QH16 + NĐ 398/2026 (29/10/2026) | 24/08/2026, kỳ 2026–2027 | Giảm 30% thuế TNDN (doanh thu ≤10 tỷ), tính **sau ưu đãi** | [Chính phủ](https://xaydungchinhsach.chinhphu.vn/toan-van-nghi-quyet-so-43-2026-qh16-ve-giam-thue-thu-nhap-ca-nhan-thue-thu-nhap-doanh-nghiep-119260830184758301.htm) |
| TNCN | **Luật 109/2025/QH15** (10/12/2025) | 01/07/2026; Đ13, Đ26 từ 01/01/2026; lương/công từ **kỳ tính thuế 2026** | Giảm **7 bậc → 5 bậc**: ≤10tr 5%, 10–30tr 10%, 30–60tr 20%, 60–100tr 30%, >100tr 35% | [Thư viện pháp luật](https://thuvienphapluat.vn/ma-so-thue/phap-luat-thue/tong-hop-diem-moi-luat-thue-thu-nhap-ca-nhan-so-1092025qh15-217745.html) · đối chiếu nội bộ `docs/runbooks/hr-tax-vn.md` (ERP-Edusuccess, `git show origin/dev:`) |
| TNCN | NQ 110/2025/UBTVQH15 | 01/01/2026, kỳ 2026 | Giảm trừ **15,5tr** bản thân, **6,2tr**/người phụ thuộc | [Luật Việt Nam](https://luatvietnam.vn/thue/nghi-quyet-110-2025-ubtvqh15-dieu-chinh-muc-giam-tru-gia-canh-thue-thu-nhap-ca-nhan-418037-d1.html) |
| TNCN | **NĐ 253/2026/NĐ-CP** + TT 87/2026 | 01/07/2026, kỳ 2026 | Thay NĐ 65/2013; chi y tế ≤23tr/năm, giáo dục ≤24tr/năm; người phụ thuộc thu nhập ≤3tr/tháng; miễn chi trả cao hơn cho làm đêm/làm thêm giờ | [EY](https://www.ey.com/content/dam/ey-unified-site/ey-com/vi-vn/technical/tax/documents/ey-decree-253-providing-guidance-on-the-implementation-of-personal-income-tax-law-109-vi.pdf) |
| BHXH | **Luật BHXH 41/2024/QH15** (29/06/2024) | 01/07/2025 | Căn cứ đóng = lương + phụ cấp + khoản bổ sung thường xuyên; **sàn = mức tham chiếu**, trần = 20 lần | [BHXH VN](https://baohiemxahoi.gov.vn:4545/File_Server_BHXH/documents/Luat%20BHXH%202024.pdf) |
| BHXH | **NĐ 161/2026/NĐ-CP** (15/05/2026) | 2,34tr đến 30/06/2026 → **2,53tr từ 01/07/2026** | Trần BHXH/BHYT 46,8tr → **50,6tr/tháng** | [Chính phủ](https://xaydungchinhsach.chinhphu.vn/tu-01-7-chinh-phu-tang-luong-co-so-119260517100243881.htm) |
| BHTN | Luật Việc làm 74/2025/QH15 + NĐ 374/2025 | 01/01/2026 | NLĐ/NSDLĐ tối đa 1%+1%; HĐLĐ từ đủ **1 tháng** (trước đây 3 tháng) | [vbpl.vn](https://vbpl.vn/en/van-ban/chi-tiet/luat-viec-lam-so-74-2025-qh15--179273) |
| Lương tối thiểu | **NĐ 293/2025/NĐ-CP** (10/11/2025) | 01/01/2026 | Vùng I–IV: **5,31 / 4,73 / 4,14 / 3,70 triệu**; thay NĐ 74/2024 | [Chính phủ](https://xaydungchinhsach.chinhphu.vn/nghi-dinh-so-293-2025-nd-cp-quy-dinh-muc-luong-toi-thieu-doi-voi-nguoi-lao-dong-lam-viec-theo-hop-dong-lao-dong-119251110172808433.htm) |
| Lương tối thiểu | NĐ 399/2026/NĐ-CP (02/11/2026) | **01/01/2027 (chưa hiệu lực)** | 5,70 / 5,08 / 4,45 / 4,04 triệu; địa bàn sáp nhập lấy mức cao nhất | [Chính phủ](https://xaydungchinhsach.chinhphu.vn/nghi-dinh-so-399-2026-nd-cp-quy-dinh-muc-luong-toi-thieu-tu-ngay-01012027-11926110315241276.htm) |
| Hóa đơn | **NĐ 254/2026/NĐ-CP** (30/06/2026) + TT 91/2026/TT-BTC | 01/07/2026 | Thay NĐ 123/2020, NĐ 70/2025, Điều 1 NĐ 41/2022; HĐ đặt in vô giá trị; biên lai giấy đến 31/12/2026; Đ10 nội dung HĐ, Đ9 thời điểm lập | [Chính phủ](https://vanban.chinhphu.vn?pageid=27160&docid=218689) · [Chính sách](https://xaydungchinhsach.chinhphu.vn/toan-van-nghi-dinh-so-254-2026-nd-cp-ve-hoa-don-dien-tu-chung-tu-dien-tu-119260713164251972.htm) |
| Địa giới | NQ 202/2025/QH15 | 34 tỉnh/thành từ 01/07/2025 | Bỏ cấp huyện; vùng lương tối thiểu theo Phụ lục NĐ 293/2025 (2026), NĐ 399/2026 (2027) | [Thư viện pháp luật](https://thuvienphapluat.vn/lao-dong-tien-luong/chinh-thuc-muc-luong-toi-thieu-vung-tu-ngay-172025-cua-28-tinh-va-6-thanh-pho-truc-thuoc-trung-uong-43622.html) |

---

## 3. Findings P0 — chặn trước khi lên production

| # | Finding | Bằng chứng `path:line` | Tác động / nguyên nhân gốc | Đề xuất (repo) |
|---|---|---|---|---|
| **P0-1** | **Ép `currency_precision = "0"` + `number_format = "#.###"` cho toàn bộ site** trong setup wizard. | `vietnam_compliance/vietnam_compliance/setup.py:104-108` (cụ thể `:107`) | Mọi phép tính kế toán bị làm tròn về số nguyên: 30.000 ÷ 7 = 4.285,71 bị biến thành 4.286 → ×7 = 30.002. ERP-Edusuccess đã phải khôi phục bằng binlog và ghi bài học; app cài/setup lại là lỗi quay lại. Nguyên nhân: nhầm "VND không có lẻ" ở mức **hiển thị chứng từ** với mức **phép tính**. | **Repo này:** xoá 2 dòng `set_single_value` cho `number_format`/`currency_precision`; chỉ để `date_format`, `time_format`, `language`. Làm tròn đúng chỗ dùng `rounding_adjustment`/`rounded_total` của ERPNext. Tham chiếu `docs/lessons/31-khong-ep-lam-tron-tang-he-thong.md:5-16,27-57` (ERP-Edusuccess). |
| **P0-2** | **Biểu thuế TNCN cũ 7 bậc** (5/10/15/20/25/30/35%, ngưỡng 5–10–18–32–52–80tr), test còn khoá luật cũ. | `payroll/pit_calculator.py:3-18`, `:36-44`, `:103-107`; `tests/test_pit_calculator.py:43-48` | Từ kỳ tính thuế 2026 luật dùng 5 bậc. Đo thực: TN tính thuế 20tr → code **2.350.000đ**, luật mới **1.500.000đ** (+850k/tháng); TN 100tr → **25.150.000đ** vs **20.500.000đ** (+4,65tr/tháng). Sai tờ khai 05/KK-TNCN. | Thay `TAX_BRACKETS` bằng 5 bậc + giảm trừ nhanh `0 / 500.000 / 3.500.000 / 9.500.000 / 14.500.000`; cập nhật docstring + test. Chốt với KTT trước khi deploy. |
| **P0-3** | **Trần BHXH/BHYT cố định 20 × 2.340.000 = 46,8tr** (NĐ 73/2024). Field `effective_date` có trong schema nhưng **không có code nào đọc**. | `payroll/insurance_calculator.py:41-44`, `:79-80`, `:91`; `vn_payroll_settings/vn_payroll_settings.json:35,53,63`; grep `effective_date` trong `payroll/` = 0 | Từ 01/07/2026 mức tham chiếu 2,53tr → trần 50,6tr. Lương 60tr vùng I: NLĐ thiếu ~304k BHXH + 57k BHYT, DN thiếu ~665k + 114k (BHYT DN 3%) ≈ **1.140.000đ/người/tháng**. Không xử lý được thay đổi giữa năm. | Nâng default `base_salary` = 2.530.000 **và** cho resolver đọc `effective_date` theo ngày tính lương (2,34tr trước 01/07/2026, 2,53tr sau). |
| **P0-4** | **Lương tối thiểu vùng dùng NĐ 74/2024** (4,96/4,41/3,86/3,45tr). | `payroll/insurance_calculator.py:45-48`, `:88-89`; `vn_payroll_settings/vn_payroll_settings.json:57-60` | Từ 01/01/2026 NĐ 293/2025: 5,31/4,73/4,14/3,70tr. Trần BHTN vùng I code 99,2tr, đúng 106,2tr → lương 100tr thu 992k thay vì 1.000k. Dataset 34 tỉnh đúng nhưng `wage_region` gắn Phụ lục cũ. | Cập nhật 4 mức NĐ 293/2025 + effective date; chuẩn bị sẵn NĐ 399/2026 cho 01/01/2027. |
| **P0-5** | **Không có idempotency khi phát hành HĐĐT.** `send_einvoice` gọi `create_and_send` trực tiếp; không dedup key, không kiểm log/SI đã phát hành. Hook tự gửi theo `on_submit`. | `e_invoicing/utils.py:126-137`; `e_invoicing/base_provider.py:203-231`; `hooks.py:50-54`; grep `dedup|deduplication|retry` trong `e_invoicing/**` rỗng | Bấm lại nút phát hành / lỗi giữa chừng → **2 hóa đơn cho 1 giao dịch** (mất tiền thật). Đây là tiêu chí nghiệm thu số 1 của ERP-Edusuccess (`AGENTS.md §3.2`). | Bắt buộc `deduplication_id`, lưu vào `VN E Invoice Log`, guard theo `(sales_invoice, trạng thái)` trước khi gọi T-VAN; retry chỉ khi đã có dedup. |
| **P0-6** | **Raw SQL dạng f-string trong 4/5 báo cáo** (S1); phần lớn value đã parameterize nhưng mẫu vẫn bị cấm tuyệt đối. | `report/vn_can_doi_phat_sinh/vn_can_doi_phat_sinh.py:50-58`, `:71-78`; `vn_so_cai/vn_so_cai.py:47-57`, `:67-77`; `vn_bang_ke_hoa_don/vn_bang_ke_hoa_don.py:48-60`; `vn_bao_cao_thue_tncn/vn_bao_cao_thue_tncn.py:40-55` | Cổng `no-raw-sql` của ERP-Edusuccess đỏ nếu tích hợp; khó review, rủi ro injection khi mở rộng. | Đổi sang `frappe.get_all`/`frappe.qb` theo mẫu đã làm đúng tại `vn_bang_luong_thang/vn_bang_luong_thang.py:22-26,97-109`. |

---

## 4. Findings P1

### 4.1 Kế toán / báo cáo

| # | Finding | Bằng chứng | Tác động | Đề xuất |
|---|---|---|---|---|
| P1-A1 | `insert(ignore_permissions=True)` tạo VAT template không comment/API key riêng/audit log (S4). | `accounting/tax_templates.py:81`, `:99` | Bypass RBAC. | Bỏ `ignore_permissions`, hoặc thêm đủ 3 điều kiện S4. |
| P1-A2 | `frappe.db.commit()` trong hook cài đặt/gỡ cài đặt (S2). | `setup.py:37`, `:44` | Phá transaction, không rollback được khi setup lỗi. | Xoá 2 dòng, để Frappe quản lý. |
| P1-A3 | Server không enforce filter dù JS `reqd:1` → gọi API thiếu `company`/kỳ vẫn chạy; `vn_so_cai` dùng `company=None` cho truy vấn đầu kỳ và **không lọc company** ở dòng entries. | JS `vn_so_cai.js:4-10` `vn_bang_ke_hoa_don.js:3-10` `vn_bao_cao_thue_tncn.js:3-10` `vn_bang_luong_thang.js:3-10`; PY `vn_so_cai.py:37-39`, `:53-55`, `:66-77`; `vn_bang_ke_hoa_don.py:37-39`; `vn_bao_cao_thue_tncn.py:29-31`; `vn_bang_luong_thang.py:133-138` | Lộ/chạm dữ liệu liên company; số dư đầu kỳ sai; `int(None)` lỗi. | `frappe.throw` ngay đầu `execute()` khi thiếu `company`/`from_date`/`to_date`; bắt buộc `company` trong mọi query. |
| P1-A4 | **Repo vendor bị nhiễm bản vá downstream**: report bảng lương mang docstring "được chép từ ERP-Edusuccess lúc build". | `vn_bang_luong_thang/vn_bang_luong_thang.py:1-5`, `:38-39`; `git log -- <file>` → commit `d466f7e` | Hai nguồn sự thật; upgrade vendor ghi đè hoặc adapter tự ngừng ghi đè ⇒ mất bản vá im lặng. | Giữ repo này nguyên bản vendor; trong ERP-Edusuccess giữ adapter `apps/bench/vendor/vietnam_compliance_report_adapters.py` làm nguồn duy nhất, hoặc upstream sửa hẳn rồi xoá adapter. |
| P1-A5 | Trùng 10 file JSON/JS giữa bộ tên ASCII và bộ tên UTF-8 (SHA256 identical, cùng `name`/`report_name`). | `vn_can_doi_phat_sinh/vn_can_doi_phat_sinh.json:10,13` vs `vn_cân_đối_phát_sinh/vn_cân_đối_phát_sinh.json:10,13` (và 4 cặp còn lại) | `migrate` import cùng 1 Report doc từ 2 file; sửa một bản gây drift. | Giữ 1 bộ JSON/JS; bộ kia chỉ giữ `.py` shim. **Đính chính:** 5 thư mục tên tiếng Việt là UTF-8 hợp lệ (`git -c core.quotepath=false ls-files`), không phải mojibake — chỉ PowerShell console hiển thị `?`; tất cả đều được git track. |
| P1-A6 | **Thiếu Bảng cân đối kế toán & Báo cáo kết quả kinh doanh**; template tài chính mặc định bị skip cho CoA VN. | `accounting/chart_of_accounts/__init__.py:147-151` (`return` sớm); `git ls-files .../report/**` chỉ có 5 report | Không có BCTC bắt buộc theo TT200/TT99 dù đã có Cân đối phát sinh & Sổ cái. | Bổ sung script report hoặc Financial Report Template cho 3 CoA; ưu tiên TT 99 (hiệu lực 01/01/2026). |
| P1-A7 | Node có con nhưng không khai `is_group` (~34 node TT200, 30 TT99, 8 TT133). | `vn_tt200.json:8-19` (`111` có `1111/1112/1113`, không có `is_group`); `vn_tt99.json:8-18`; `vn_tt133.json:20-31`; chỉ 6 root có `is_group:1` (`vn_tt200.json:5-7,273-275,438-440,504-506,556-558,703-705`) | Nếu ERPNext không tự set khi build tree ⇒ tài khoản tạo dạng ledger, không gom số dư, cân đối phát sinh sai. **Cần xác minh trên site** trước khi sửa (`bench console`: đọc `is_group` của `111 - Tiền mặt - <abbr>`). | Thêm `"is_group": 1` cho mọi node có children, hoặc ghi rõ giả định đã kiểm chứng. |

### 4.2 Lương / thuế / BHXH

| # | Finding | Bằng chứng | Tác động | Đề xuất |
|---|---|---|---|---|
| P1-B1 | **Không có sàn đóng BHXH/BHYT** (= mức tham chiếu): hàm chỉ có `min(salary, ceiling)`. | `insurance_calculator.py:91-92` | `insurance_salary` = 0/thấp (thử việc, thiếu dữ liệu) → đóng 0, vi phạm Luật BHXH 2024. | `base = max(floor, min(salary, ceiling))`. |
| P1-B2 | **Không có lũy kế tháng / quyết toán năm**; hook chỉ đóng `gross_pay` tháng vào hàm tháng. | `pit_calculator.py:47-117`; `payroll/utils.py:177-181` | Khấu trừ lệch khi thu nhập không đều; báo cáo thuế sai; Luật 109 áp từ kỳ 2026. | Thêm cumulative withholding + annual reconciliation; tách "thuế tạm tính" và "thuế quyết toán". |
| P1-B3 | Giảm trừ mới NĐ 253/2026 (y tế ≤23tr/năm, giáo dục ≤24tr/năm) chưa có; field `meal_allowance_exempt = 730.000` **chỉ nằm trong JSON, không code nào đọc**. | `vn_payroll_settings.json:11,38`; `pit_calculator.py:53,90-95` (chỉ có `other_deductions` tự do) | NLĐ bị thu thêm tối đa 47tr/năm; field cấu hình chết. | Thêm 2 khoản có trần/năm; dùng hoặc bỏ field phụ cấp ăn. |
| P1-B4 | KPCĐ luôn tính trên lương cá nhân, không trên quỹ lương (hàm tự gọi là "approximation"). | `payroll/utils.py:176`; `insurance_calculator.py:62,70-72,103-104` | Quỹ KPCĐ sai (thường thấp hơn 2% quỹ lương). | Tính tổng quỹ lương kỳ rồi truyền `total_payroll`. |
| P1-B5 | Vùng lương lấy từ `employee.vn_province`, trong khi NĐ 293/2025 xác định theo địa bàn hoạt động của NSDLĐ/chi nhánh. | `payroll/utils.py:165-171`; `vn_province/vn_province.json:32-38` | Trần BHTN áp sai cho NLĐ làm việc khác vùng nơi đăng ký. | Lấy vùng từ Company/chi nhánh. |

### 4.3 HĐĐT / mẫu in

| # | Finding | Bằng chứng | Tác động | Đề xuất |
|---|---|---|---|---|
| P1-C1 | **HTTP 200 + lỗi nghiệp vụ T-VAN bị coi là thành công**: 5 provider chỉ `raise_for_status()` rồi lấy id; response thiếu field → `draft_id=""` nhưng vẫn log `"Accepted"` và set SI `"Đã phát hành"` với số HĐ rỗng. | `viettel.py:86-98`, `vnpt.py:49-61`, `misa.py:63-75`, `fpt.py:65-76`, `bkav.py:64-74`; `base_provider.py:212-230,237-249` | In HĐ "thành công" nhưng không có số; nút phát hành hiện lại (`public/js/vn_einvoice.js:5`) → cộng hưởng thành **P0 duplicate**. | Parse mã lỗi/field bắt buộc; throw nếu thiếu `invoice_number`; chỉ set "Đã phát hành" khi có số. |
| P1-C2 | `@frappe.whitelist()` không khai `methods` trên 2 endpoint ghi (S5). | `e_invoicing/utils.py:126`, `:140` | Endpoint ghi có thể bị gọi bằng GET (verb mặc định **CHƯA XÁC MINH** — không có source Frappe trong repo). | `@frappe.whitelist(methods=["POST"])`. |
| P1-C3 | `poll_pending_invoices` là **code chết + đói hàng đợi**: lọc `status="Pending"` nhưng `_log_success` hardcode `Accepted`, `_log_failure` `Rejected`, cancel `Cancelled`; `limit=50`, không con trỏ. | `e_invoicing/utils.py:86-119` (`:90`, `:92`); `base_provider.py:237-262`; `vn_e_invoice_log.json:30`; `hooks.py:124-127` | Luồng poll/get_status không bao giờ chạy; >50 bản ghi Pending thì phần sau không được xét. | Tạo log `Pending` sau `create_draft` cho provider async; thêm `order_by`/cursor hoặc lọc `creation < now - X`. |
| P1-C4 | Mẫu Hóa đơn bán hàng gọi `invoice_qr_data_uri_optional(doc.name)` nhưng repo này **không định nghĩa/cũng không đăng ký Jinja**; helper nằm ở `smart_edu_core`. | `print_format/vn_hoa_don_ban_hang/vn_hoa_don_ban_hang.json:11`; `hooks.py:79-84` (chỉ `so_tien_bang_chu`, `format_vnd`); ERP: `apps/smart_edu_core/smart_edu_core/utils/vietqr.py:338`, `hooks.py:321-325`; test chỉ assert chuỗi `tests/test_print_format_content.py:37-40` | Trên stack Edusuccess chạy được; cài app độc lập → Jinja undefined khi in (lỗi runtime **CHƯA XÁC MINH** trên site thật). | Định nghĩa helper fail-soft ngay trong app này + đăng ký vào `hooks.py:79-84`, hoặc bỏ QR khỏi template mặc định. |
| P1-C5 | **Cross-repo: 3 nơi đặt `default_print_format`** cho cùng `Sales Invoice`/`Payment Entry`. App dùng `field_name="default_print_format"`, ERP dùng `field_name=""` + `doctype_or_field="DocType"` ⇒ tạo 2 Property Setter khác nhau cho cùng 1 DocType; app cũng gọi ở `after_install` (không chạy lại khi nâng cấp). | `vietnam_compliance/print_format_defaults.py:14-19`, `:65-85`; `setup.py:25-37`; ERP `git show origin/dev:apps/smart_edu_core/smart_edu_core/print_format_defaults.py` và `hooks.py` (`ensure_einvoice_print_format` + `ensure_vn_print_format_defaults`) | Hai nguồn sự thật; Property Setter của app có thể không có hiệu lực (field-level thay vì DocType-level — cần xác minh trên site). | Chọn 1 owner. Đề xuất: app chỉ cung cấp Print Format, ERP giữ thiết lập default; hoặc app sửa đúng filter rồi gỡ hook ERP. |

---

## 5. Findings P2 (tóm tắt)

| Nhóm | Finding | Bằng chứng |
|---|---|---|
| Kế toán | `@frappe.whitelist()` thiếu `methods` | `accounting/chart_of_accounts/__init__.py:41-42` |
| Kế toán | Dùng `float`/`round(...,2)` cho tiền VND | `vn_can_doi_phat_sinh.py:48,59,79-95`; `vn_bang_ke_hoa_don.py:64-66` |
| Kế toán | Lọc kỳ thuế TNCN sai (`start_date >= from_date AND end_date <= to_date`, group theo NV không theo tháng) | `vn_bao_cao_thue_tncn/vn_bao_cao_thue_tncn.py:32-37,50` |
| Kế toán | PII (MST) hiện diện rộng; role `Accounts User`/`Accounts Manager` | `vn_bang_ke_hoa_don.py:24,73` + JSON `:16`; `vn_bao_cao_thue_tncn.py:20,59,63` + JSON `:18` |
| Kế toán | VAT template: check tồn tại theo `f"{title} - {abbr}"` nhưng tạo doc với `"title": vat["title"]`; `_find_account` trả `None` không guard; exception bị nuốt | `tax_templates.py:65-66,70,102-112`; `setup.py:100-101` |
| Kế toán | **Không có test nào** cho 5 report / 3 CoA (không chứng minh ∑Nợ = ∑Có) | `git ls-files \| grep test` |
| Lương | Config `0` bị bỏ qua (`if value:`), lỗi đọc settings nuốt im | `insurance_calculator.py:128-133`; `pit_calculator.py:134-146` |
| Lương | Region không hợp lệ rơi im lặng về "I" (trần cao nhất) | `insurance_calculator.py:88` |
| Lương | CCCD **không kiểm checksum**; `mask_cccd` chỉ dùng trong test | `payroll/cccd.py:37-40,43-48`; `tests/test_cccd.py:34-36` |
| Lương | Làm tròn `round()` Python (banker's rounding), sai tối đa 1đ; thiếu xử lý thu nhập khác/miễn thuế | `pit_calculator.py:53,90-96,98-99,109` |
| HĐĐT | Có timeout nhưng **không retry** | `viettel.py:46-54,87`; `vnpt.py:50-56`; `misa.py:32-41`; `fpt.py:32-43`; `bkav.py:33-42`; `utils.py:63-72` |
| HĐĐT | Hủy set "Đã hủy" vô điều kiện dù T-VAN có thể từ chối (HTTP 200) | `utils.py:152-165`; `vnpt.py:89-102`, `misa.py:98-110`, `fpt.py:107-116`, `bkav.py:105-117`, `viettel.py:133-151` |
| HĐĐT | NĐ 254: `tax_authority_code`, thời gian ký, XML/PDF đã ký **có schema nhưng không bao giờ được ghi**; 4/5 provider trả `invoice_date=""`; field SI kiểu `Date` | `vn_e_invoice_settings.json:53`; `vn_e_invoice_log.json:39,42-45`; grep rỗng; `viettel.py:108`, `vnpt.py:68`, `misa.py:82`, `bkav.py:81`; `setup.py:335-337` |
| HĐĐT | **Điều chỉnh hóa đơn chưa có** luồng gọi (chỉ abstract + implement provider) | `base_provider.py:104-106`; grep `.replace(` rỗng; `setup.py:303` |
| HĐĐT | Ghi chú KCT áp cho **mọi HĐ có thuế = 0**, kèm căn cứ cố định "khoản 13 Điều 5 Luật 48/2024" | `vn_hoa_don_ban_hang.json:11`; `setup.py:344-352`; `tests/test_print_format_content.py:22-28` |
| HĐĐT | Test default print format là **pass rỗng** cho Purchase Invoice (map tới "VN Hóa Đơn Mua Hàng" nhưng repo chỉ có `vn_don_mua_hang`) | `print_format_defaults.py:14-19`; `tests/test_print_format_defaults.py:55-73` |
| HĐĐT | Provider status mapping thiếu nhánh `rejected`; VNPT map mọi giá trị khác `published` → `pending` | `vnpt.py:72-87`; `fpt.py:93-105`; `utils.py:112-118` |
| HĐĐT | Response lỗi thô có thể lọt Error Log (S7) | `viettel.py:63-65`; `misa.py:47-49`; `fpt.py:49-51`; `bkav.py:48-50`; `utils.py:68` |
| HĐĐT | Viettel **đoán** mã thuế từ `api_username` | `viettel.py:133-135` |
| Khác | Thiếu CoA TT 58/2026 cho DN siêu nhỏ (từ 01/07/2026) | `setup.py:197` chỉ có TT99/TT200/TT133; baseline mục 2 (cần đối chiếu bản gốc TT 58) |
| Khác | Docstring `load_provinces` ghi 63 tỉnh; fixture thực tế **34** (đo `json.load` → `len=34`) | `setup.py:117`; `fixtures/provinces.json` |
| Khác | `S2/S4/S5` rải rác (đã liệt kê ở P1/P0 nhưng phạm vi rộng hơn) | `setup.py:138,163,373`; `base_provider.py:249,262`; `utils.py:165`; `print_format_defaults.py:85` |

---

## 6. Điểm mạnh đã kiểm chứng (không nên sửa lại)

1. **Bản vá bảng lương là mẫu S1 đúng** — `frappe.get_all`, docstring giải thích "tại sao" kèm bằng chứng đo staging; gom `Salary Detail` một truy vấn; tên khoản lương đọc từ Site Config (`vn_bang_luong_thang.py:1-40,63-74,86-109`).
2. **Cân đối phát sinh có kiểm soát server** — `frappe.throw` khi thiếu company (`:18-20`), lọc `is_group:0, disabled:0` (`:33-38`), `is_cancelled = 0` (`:54,63`), công thức `closing = opening + debit - credit` đúng (`:81`), tách Dư Nợ/Có (`:90-95`).
3. **Chứng từ submitted được lọc** — `inv.docstatus = 1` (`vn_bang_ke_hoa_don.py:35`), `ss.docstatus = 1` (`vn_bao_cao_thue_tncn.py:27`), `is_cancelled = 0` (`vn_so_cai.py:34`).
4. **CoA có `account_type` đúng** cho tài khoản đặc thù; `33311`, `1331`, `6428` **có trong cả 3 bộ CoA** (`vn_tt200.json:286-289,62-65,683-686`; `vn_tt99.json:246-249,54-57,541-544`; `vn_tt133.json:100-103,23-26,270-273`) — regional override `hooks.py:90-96` không thiếu tài khoản. Docstring `tax_templates.py:8-9` nói chỉ TT200/TT99 là understated (TT133 cũng có).
5. **F-06..F-10 đã đóng ở HEAD hiện tại** — switch `enabled` mặc định 0 + validate fail-closed (`vn_e_invoice_settings.json:33,54,56`, `.py:17-24`), cờ `vn_is_kct` (`setup.py:344-352`), CSS có nội dung ở 8/8 mẫu (`vn_hoa_don_ban_hang.json:23`, `tests/test_print_format_css_field.py:36-51`), default print format chạy từ `after_install` (`setup.py:25-37`). Không báo lại finding cũ.
6. **Fixture 34 tỉnh đúng NQ 202/2025** (đo trực tiếp), regional override CoA đăng ký rõ (`hooks.py:102-112`).

---

## 7. Kiểm chứng cần chạy trên VPS staging (KHÔNG chạy local — `AGENTS.md §7.1`)

1. `bench --site <s> console` → đọc `frappe.get_single("VN Payroll Settings")` xem admin đã sửa tay `base_salary`/`min_wage_region_*` chưa; nếu đã sửa thì mức độ P0-3/P0-4 giảm, nhưng **vẫn thiếu cơ chế `effective_date`**.
2. Đếm bản ghi `VN Employee Tax Info` / `Salary Slip` có dùng custom field thật không; kiểm tra Salary Structure có deduction component "BHXH (NLĐ 8%)"/"Thuế TNCN" hay có **hai nguồn tính** làm lương thực lĩnh lệch (`payroll/utils.py:183-185` chỉ ghi 3 field read-only, không đụng `total_deduction`/`net_pay` — rủi ro có thể P0).
3. `frappe.get_doc("Report","VN Sổ Cái").report_name` + `frappe.get_module(...)` — xác nhận shim UTF-8 được import thật; `frappe.get_meta("Account").autoname` + `get_value("Account","111 - Tiền mặt - <abbr>","is_group")`; `frappe.db.get_table_columns("GL Entry")`.
4. Sau setup wizard: đếm template thuế trùng; kiểm tra Property Setter `default_print_format` thực ra nằm ở bản app hay bản ERP (finding P1-C5).
5. Chạy 5 report với số liệu thật: đối chiếu ∑Nợ − ∑Có = 0; kiểm tra field `vn_einvoice_number`, `vn_tax_code`, `vn_pit_amount`.
6. Render PDF 8 mẫu (computed style, KCT, MST) — không chỉ kiểm tồn tại file/CSS.
7. Đối chiếu endpoint/response/mã lỗi của 5 T-VAN với tài liệu vendor — repo tự thừa nhận chưa làm (`docs/AUDIT_SVN_FINDINGS_20261120.md:34`).
8. Chạy lại gates ERP-Edusuccess (`no-raw-sql`, `no-commit-in-api`, `whitelist-methods`, `no-permission-bypass`) nếu copy code sang; **CHƯA CHẠY**.

## 8. Tests/validation cần bổ sung (trước khi đóng finding)

| Nhóm | Test |
|---|---|
| Tiền tệ | Assert `System Settings.currency_precision` **không bị đặt** bởi setup wizard; `fmt_money(4285.71)` vẫn giữ 2 lẻ (theo `docs/lessons/31-...:27-57`) |
| Thuế TNCN | Parameterized test 5 bậc mới: 4tr→200k, 14,5tr→950k, 20tr→1,5tr, 50tr→6,5tr, 100tr→20,5tr; test phải ĐỎ trên bảng 7 bậc cũ |
| BHXH | Test effective date: ngày 30/06/2026 → trần 46,8tr; 01/07/2026 → 50,6tr; test sàn `insurance_salary = 0` → vẫn đóng theo tham chiếu |
| Lương tối thiểu | Test 4 vùng NĐ 293/2025 + region không hợp lệ phải `throw` (không rơi về "I") |
| HĐĐT | Test dedup: gọi `send_einvoice` 2 lần với cùng `deduplication_id` → chỉ 1 log, 1 lần gọi provider; test HTTP 200 thiếu `invoice_number` → KHÔNG set "Đã phát hành" |
| Báo cáo | Test ∑Nợ = ∑Có trên fixture GL Entry; test `execute()` thiếu `company` phải `throw`; test lọc kỳ overlap |
| Print format | Test default cho Purchase Invoice phải đọc danh sách Print Format thật (không stub tùy ý); test Jinja helper tồn tại trong app khi cài độc lập |

## 9. Next steps / owner

| Ưu tiên | Việc | Owner | Nơi sửa |
|---|---|---|---|
| 1 (P0) | Xoá ép `currency_precision`; 5 bậc TNCN; trần 2,53tr + effective date; NĐ 293; idempotency HĐĐT | Kỹ thuật app + **KTT ký** thuế | `vietdungiitb/vietnam-compliance` (AGENTS.md §2.2 — KHÔNG workaround trong `smart_edu_core`) |
| 2 (P0) | Thay 4 report raw SQL bằng `frappe.get_all` | Kỹ thuật app | repo này |
| 3 (P1) | Parse lỗi nghiệp vụ T-VAN + `methods=["POST"]` + log Pending | Kỹ thuật app | repo này |
| 4 (P1) | Chọn 1 owner cho default print format; gộp JSON/JS trùng; quyết định adapter bảng lương | Owner app + ERP-Edusuccess | cả 2 repo |
| 5 (P1) | Bổ sung BCTC (TT 99) + test ∑Nợ=∑Có | Kỹ thuật app + KTT | repo này |
| 6 | Chạy 8 mục staging + cập nhật `docs/COMPLIANCE-VN.md` (ERP) vốn còn ghi "CHƯA TÍCH HỢP" dù hook HĐĐT đã có (`AGENTS.md`-ERP `hooks.py:361-368`) | PM/DevOps | ERP-Edusuccess (cross-repo handoff) |

> **Production gate:** mọi mục thuế (P0-2/P0-3/P0-4, P1-B3, KCT) phải có chữ ký KTT; sandbox
> PM-SB-01..19 cho phép giả định đã duyệt, khi lên production ngoại lệ hết hiệu lực.

---

*Tài liệu là bằng chứng theo `documentation-evidence-rule.md`. Không có thay đổi code trong phiên audit này; `git status` của cả 2 repo không có file code nào bị sửa.*

---

## 10. AUDIT ĐỘC LẬP PLAN — 26/11/2026 (phần bổ sung, không ghi đè mục 1–9)

> **Đối tượng:** `docs/PLAN_COMPLIANCE_VN_20261126.md` · **HEAD:** `cd2d7ec04269e507f0504e20d175dafcf43e8709`,
> `origin/main...HEAD = 0 0` · **Vai trò:** auditor chỉ đọc, không sửa code, không commit; chỉ append mục này
> vào file audit có sẵn.

### 10.1 VERDICT: **NEED_REVISION**

Lý do: 5 objection (O1–O5) làm AC/base-line không đo được hoặc pass rỗng; O6–O7 là đính chính số.
Sửa xong O1–O5 có thể chuyển `AGREE`. Không `REJECT`: 6/6 finding P0 đều nằm trong SCOPE.

### 10.2 Objection (đánh số, kèm `path:line`)

| # | Mức | Objection | Bằng chứng / cách sửa |
|---|---|---|---|
| **O1** | Blocker | Baseline plan sai số. `PLAN:14` ghi lệnh `pytest tests/ vietnam_compliance/tests/ -q → 14 passed, 8 subtests`. Thực chạy: **25237 passed, 8 subtests (82,52s)**. `14 passed, 8 subtests` chỉ đúng với riêng `vietnam_compliance/tests/`. | `tests/test_translations_csv.py` parametrize **25223** ca (`pytest tests/ --collect-only -q` → `25223 tests collected`; `vietnam_compliance/tests/` → `14 tests collected`). `AUDIT:16` đúng vì chỉ chạy thư mục app. Sửa `PLAN:14` thành 2 dòng tách biệt hoặc ghi đúng 25237. |
| **O2** | Blocker | REQ-07 (`PLAN:51`) đòi grep sạch S2/S4/S5 nhưng SCOPE (`PLAN:22-26`) **thiếu 2 file** chứa vi phạm. | `vietnam_compliance/accounting/tax_templates.py:81,99` (2× `ignore_permissions=True`); `vietnam_compliance/accounting/chart_of_accounts/__init__.py:41` (`@frappe.whitelist()` không `methods`). Grep thực toàn app: **11** `ignore_permissions`, **2** `frappe.db.commit()` (`setup.py:37,44`), **3** whitelist trần (`chart_of_accounts/__init__.py:41`, `e_invoicing/utils.py:126,140`). Thêm 2 file vào SCOPE + task T6, hoặc thu hẹp REQ-07. |
| **O3** | Blocker | REQ-07 nới S4: `PLAN:51` chỉ cần "comment+audit", thiếu **API key riêng**. | `AGENTS.md:96` (ERP-Edusuccess) bắt buộc 3 điều kiện: comment giải thích + API key riêng + audit log. Các chỗ hiện tại (`print_format_defaults.py:85`, `base_provider.py:249,262`, `e_invoicing/utils.py:165`, `tax_templates.py:81,99`) không có cả 3. Sửa AC thành đúng S4. |
| **O4** | Blocker | REQ-10 (`PLAN:54`) chọn app làm owner default print format nhưng non-goal `PLAN:37` cấm sửa `smart_edu_core`; hook ERP vẫn ghi cùng Property Setter ⇒ 2 nguồn sự thật. | `git show origin/dev:apps/smart_edu_core/smart_edu_core/hooks.py` vẫn có `smart_edu_core.print_format_defaults.ensure_vn_print_format_defaults`; hàm này dùng filter `{"doctype_or_field":"DocType","field_name":"","property":"default_print_format"}` y hệt REQ-10. Muốn "không trùng bản ERP" phải gỡ hook ERP (PR riêng, bỏ non-goal cho slice này) **hoặc** đảo REQ-10: app giữ field-level, ERP làm owner. |
| **O5** | Material | REQ-03 (`PLAN:47`) chỉ test `calculate_insurance(as_of=...)`; caller thật không truyền ngày ⇒ effective-date không áp vào payroll. | `vietnam_compliance/payroll/insurance_calculator.py:59-63` không có tham số `as_of`; `vietnam_compliance/payroll/utils.py:176` gọi `calculate_insurance(insurance_salary, wage_region)`. Thêm AC: caller truyền `doc.start_date`/`posting_date` + test runtime (stub) cho kỳ 30/06 và 01/07/2026. |
| **O6** | Minor | Sai số học trong P0-3. | `AUDIT:76` ghi "DN thiếu ~665k + 57k ≈ **1.083.000đ**". Theo `insurance_calculator.py:52-53` (SI DN 17,5%, BHYT DN 3%) và Δ trần 3,8tr: DN BHYT = **114k**, tổng = **1.140.000đ**. NLĐ 304k/57k đã đúng. Sửa `AUDIT:76`. |
| **O7** | Minor | Sai số dòng. | `AUDIT:74` ghi "xoá **3** dòng `set_single_value` cho `number_format`/`currency_precision`"; source `vietnam_compliance/vietnam_compliance/setup.py:106-107` chỉ có **2** dòng (`:108` là `language`, giữ lại). |

### 10.3 Đối chiếu số pháp lý — khớp, có 1 mức tin cậy cần nói rõ

- **5 bậc TNCN + giảm trừ nhanh:** `PLAN:46`, `AUDIT:57,175` khớp baseline ERP `git show origin/dev:docs/runbooks/hr-tax-vn.md` mục 1.2 (10/30/60/100tr; 5/10/20/30/35%; 15,5/6,2tr). Bộ giảm trừ nhanh `0 / 0,5 / 3,5 / 9,5 / 14,5tr` tự nhất quán tại ranh giới: 10tr×10%−0,5 = 0,5tr; 30tr×20%−3,5 = 2,5tr; 60tr×30%−9,5 = 8,5tr; 100tr×35%−14,5 = 20,5tr = 100tr×30%−9,5.
- **Trần BHXH 46,8tr → 50,6tr** (`AUDIT:61`, `PLAN:47`) = 20×2,34tr → 20×2,53tr; source cũ `insurance_calculator.py:42`. **Lương tối thiểu 5,31/4,73/4,14/3,70tr** (`AUDIT:63`, `PLAN:48`) so với source cũ `insurance_calculator.py:45-48` (4,96/4,41/3,86/3,45tr).
- **TT 99 hiệu lực 01/01/2026** (`AUDIT:48`) và **NĐ 254 từ 01/07/2026** (`AUDIT:65`) khớp `git show origin/dev:docs/COMPLIANCE-VN.md` ("Nghị định 254/2026/NĐ-CP … hiệu lực từ 01/7/2026").
- ⚠️ **CHƯA XÁC MINH độc lập:** phiên này không mở lại các link `.gov.vn` trong `AUDIT:44-66`; việc đối chiếu ở trên là **khớp nội bộ** plan ↔ audit ↔ baseline ERP ↔ arithmetic, không phải xác nhận văn bản gốc. Giữ nguyên cảnh báo trước khi KTT ký.

### 10.4 Test ĐỎ trên code cũ — đo được 1, phần còn lại CHƯA CHẠY

- Đã chạy (thuần Python, `-B`, không Docker, worktree sạch):
  `python -B -c "... calculate_pit(31_000_000,0,0,11_000_000,4_400_000) ... assert tax==1_500_000"`
  → `taxable 20000000 tax 2350000 bracket 4`, `AssertionError`. **ĐỎ đúng như `AUDIT:75` / `PLAN:46`.**
- REQ-03/04/05/09/10 sẽ ĐỎ vì chữ ký/template hiện tại (`insurance_calculator.py:59-63`, `:88`; `e_invoicing/utils.py:126-137`; `print_format_defaults.py:80`; `vn_hoa_don_ban_hang.json:11`) — nhưng **test mới chưa tồn tại ⇒ CHƯA CHẠY**, không báo PASS.
- REQ-06 là grep, không phải pytest; hiện grep `frappe.db.sql` trong `report/**` cho 10 hits ở 4 file ASCII (`vn_can_doi_phat_sinh.py:50,71-72`; `vn_so_cai.py:47,67-68`; `vn_bang_ke_hoa_don.py:48-49`; `vn_bao_cao_thue_tncn.py:40-41`) — ĐỎ nếu viết test quét. Bản UTF-8 trùng tên chỉ là shim, không chứa SQL.

### 10.5 Phạm vi P0 / non-goals

Đủ **6/6 P0**: P0-1→REQ-01, P0-2→REQ-02, P0-3→REQ-03, P0-4→REQ-04, P0-5→REQ-05, P0-6→REQ-06 (`AUDIT:74-79` ↔ `PLAN:45-50`). Non-goals (`PLAN:31-37`) hợp lý: TT58 thiếu bản gốc, cumulative PIT/BCTC cần KTT chọn phương án, site-test để `CHƯA CHẠY`. **Không có P0 nào bị bỏ sót**; lỗ hổng nằm ở AC (O2/O3/O5), không ở danh sách finding.

### 10.6 Quyền "owner" vs KTT, và xung đột AGENTS.md

- `PLAN:4-6` tự ghi `OWNER-APPROVED-20261126` nhưng **không có file quyết định/ký tên** trong repo làm bằng chứng. `AGENTS.md:141` bắt buộc kế toán trưởng xác nhận mọi đổi thuế; `docs/QUYET-DINH-PM-SANDBOX.md` (origin/dev, PM-SB-39/-53) nói rõ uỷ quyền chat **chỉ sandbox**, production ký thật. ⇒ Chấp nhận owner quyết **phạm vi/process khi development**, **không** thay chữ ký KTT cho P0-2/3/4, P1-B3, KCT. Reservation: trước B5 ghi quyết định owner có tên+ngày vào `docs/`; trước production KTT ký thật.
- `AGENTS.md:81` (§2.2) sửa trong repo vendor, không workaround `smart_edu_core` → `PLAN:37` tuân thủ; **ngoại lệ O4** phải xử lý bằng PR gỡ hook ở repo ERP, tuyệt đối không viết workaround ngược trong `smart_edu_core`.
- `AGENTS.md:283` (§7.1) cấm test có site trên local Docker → `PLAN:36` tuân thủ. Pytest thuần đã chạy ở trên không dùng Docker, không tạo file (`git status --short` vẫn chỉ 3 file `docs/**` untracked có sẵn). Migrate/schema (xem R1) phải lên VPS staging, khoá claim `ENV-STAGING`.

### 10.7 Reservation — ai đóng, bước nào

| Reservation | Người đóng | Bước đóng |
|---|---|---|
| R1 — `deduplication_id` chưa có schema: `vn_e_invoice_log.json:7-24` không có field; unit test chỉ chứng minh logic, không chứng minh lưu/đọc lại. | Dev app + Ops | Sau merge, thêm field + `bench migrate` trên **VPS staging**, khoá `ENV-STAGING` trước khi chạy. |
| R2 — O5 caller effective-date. | Dev app | Trước khi đóng REQ-03 (B6). |
| R3 — O4 owner default print format. | PM ERP + owner app | Trước B5 (đồng thuận), PR riêng trên `dev` ERP nếu chọn gỡ hook. |
| R4 — O1 baseline. | Tác giả plan | Sửa `PLAN:14` trước B5. |
| R5 — nguồn luật gốc chưa mở lại. | Auditor/owner | Trước lúc KTT ký production. |

> Auditor: chỉ append mục 10. Không sửa `PLAN_*`, không sửa code, không commit, không chạy test cần site.

---

## 11. Trạng thái sau khi xử lý (26/11/2026, nhánh `fix/compliance-vn-20261126`)

Auditor độc lập re-audit vòng 2: **AGREE** — 0 blocker, 0 major. Các objection O8–O13 đã đóng
(bằng chứng trong báo cáo re-audit của auditor; tự chạy lại lệnh, không tin lời người sửa).

| REQ | Trạng thái | Bằng chứng chính |
|---|---|---|
| REQ-01 Bỏ ép precision | ĐÃ SỬA | `setup.py:104-110` |
| REQ-02 PIT 5 bậc | ĐÃ SỬA | `pit_calculator.py:37-44,103-115` |
| REQ-03 BHXH effective-date + `as_of` | ĐÃ SỬA | `insurance_calculator.py:162-197`, `payroll/utils.py:170,178-180` |
| REQ-04 NĐ 293/2025 + sàn | ĐÃ SỬA | `insurance_calculator.py:46-49,127-133`, JSON `:35,57-60` |
| REQ-05 Idempotency HĐĐT | ĐÃ SỬA (logic) | `vn_e_invoice_log.json:17,40`, `base_provider.py:212-265`, `utils.py:94,118-134` |
| REQ-06 Hết raw SQL | ĐÃ SỬA | 4 report dùng `frappe.get_all` |
| REQ-07 S2/S4/S5 | ĐÃ SỬA (S4 còn R-OPS) | `setup.py:37-45`, `tax_templates.py:71-111`, `chart_of_accounts/__init__.py:41` |
| REQ-08 Company + kỳ overlap | ĐÃ SỬA | 4 report + `payroll/utils.py:227-228` |
| REQ-09 KCT theo cờ | ĐÃ SỬA | `vn_hoa_don_ban_hang.json:11` |
| REQ-10 Print format filter | ĐÃ SỬA (schema) | `print_format_defaults.py:71-85` |

**Đã chạy:** `pytest tests/ vietnam_compliance/tests/ -q` → **25267 passed, 8 subtests**;
`ruff check vietnam_compliance/ tests/` → All checks passed; `compileall -q` → exit 0;
JSON validation → OK; kiểm 25 file sửa → 0 ký tự `U+FFFD`.
Fail-before gốc: 26 failed / 2 passed trước khi sửa (`tests/test_compliance_2026.py`).

**CHƯA CHẠY / CHƯA XÁC MINH (chuyển tiếp, không báo PASS):**
- `bench migrate` VPS staging cho field `deduplication_id` unique (khoá `ENV-STAGING`, đếm log cũ).
- `against_account` trong GL Entry; hội tụ Property Setter; render PDF 8 mẫu; 5 provider T-VAN;
  gates ERP-Edusuccess; O13 (hai nguồn tính lương) — backlog riêng.

## 12. Quyết định cuối của owner — pre-production (26/11/2026)

Owner dự án ra chỉ thị: **không chờ KTT** (hiện chưa có KTT chính thức), tự quyết theo đúng
quy trình để hoàn thiện dự án. Mục 10.6/10.7 ở trên là reservation của auditor ở thời điểm
đó; giờ được owner chốt lại như sau:

| Reservation cũ | Quyết định owner |
|---|---|
| R-OPS: service account cho 6 chỗ `ignore_permissions=True` | **ĐÓNG**: bỏ hoàn toàn `ignore_permissions=True`; cấp `create/write` cho `Accounts User`/`Accounts Manager` trên `VN E Invoice Log` (RBAC thật) |
| KTT ký thuế/BHXH/KCT | **OWNER-APPROVED-FINAL** cho pre-production (`docs/OWNER-DECISION-20261126.md`); KTT khi có ở production sẽ yêu cầu thay đổi nếu cần |
| R5: đối chiếu văn bản gốc | Baseline đã tra cứu từ nguồn `.gov.vn` ở mục 2; owner chấp nhận dùng baseline này cho pre-production |
| R1: migrate staging | Vẫn là bước kỹ thuật bắt buộc — thực hiện cùng phiên này, khoá `ENV-STAGING` |

Không còn gate chờ người khác để đưa hệ thống vào chạy pre-production.
