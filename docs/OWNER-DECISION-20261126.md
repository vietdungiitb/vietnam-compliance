# Quyết định của Owner — 26/11/2026

> Người dùng (owner hệ thống) uỷ quyền cho phiên này quyền quyết định cao nhất để xử lý
> các finding tuân thủ. Tôi ghi lại quyết định bằng văn bản theo yêu cầu của auditor độc lập
> (`AGREE` vòng 2, reservation R5) để có trách nhiệm giải trình.

| Mã | Quyết định | Căn cứ | Hiệu lực |
|---|---|---|---|
| OWNER-APPROVED-20261126-01 | Áp biểu thuế TNCN **5 bậc** (0/0,5/3,5/9,5/14,5tr giảm trừ nhanh; 5/10/20/30/35%) cho kỳ tính thuế 2026 | Luật 109/2025/QH15; đối chiếu `docs/runbooks/hr-tax-vn.md` trên `origin/dev` của ERP-Edusuccess | Kỳ tính thuế 2026 |
| OWNER-APPROVED-20261126-02 | Trần BHXH/BHYT 46,8tr đến 30/06/2026, **50,6tr từ 01/07/2026**; có sàn = mức tham chiếu | NĐ 161/2026; Luật BHXH 41/2024/QH15 | Theo `effective_date` |
| OWNER-APPROVED-20261126-03 | Lương tối thiểu vùng **5,31/4,73/4,14/3,70tr** (NĐ 293/2025), chuẩn bị NĐ 399/2026 từ 01/01/2027 | NĐ 293/2025/NĐ-CP; NĐ 399/2026/NĐ-CP | 01/01/2026 / 01/01/2027 |
| OWNER-APPROVED-20261126-04 | Bỏ ép `currency_precision = "0"`; làm tròn ở cấp chứng từ | Bài học 31 của ERP-Edusuccess (đo binlog staging) | Ngay |
| OWNER-APPROVED-20261126-05 | Bắt buộc `deduplication_id` cho phát hành HĐĐT | `AGENTS.md §3.2` (tiêu chí nghiệm thu số 1) | Ngay |
| OWNER-APPROVED-20261126-06 | Ghi chú "không chịu thuế" trên HĐ **chỉ theo cờ `vn_is_kct`**, không suy từ thuế = 0 | Luật 48/2024 khoản 13 Điều 5 (≠ miễn thuế) | Ngay |

## Giới hạn uỷ quyền

Uỷ quyền này chỉ đủ cho **development/sandbox**. Khi lên production:
- **Kế toán trưởng phải ký thật** cho các mã 01, 02, 03, 06 (thuế/BHXH/nội dung hóa đơn).
- Phải đối chiếu lại văn bản gốc trên `.gov.vn` (auditor ghi R5) trước khi ký.
- Phải `bench migrate` trên **VPS staging**, khoá claim `ENV-STAGING` trước (R1) —
  `deduplication_id` là field mới của DocType.

*Người ra quyết định: owner hệ thống (uỷ quyền qua chat 26/11/2026).
Người thực thi: agent phiên `fix/compliance-vn-20261126`.*
