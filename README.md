# Vietnam Compliance — Ứng dụng Tuân thủ Pháp lý & Bản địa hóa Việt Nam cho Frappe / ERPNext v16

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Frappe Framework](https://img.shields.io/badge/Frappe-v16-orange.svg)](https://frappeframework.com/)
[![ERPNext](https://img.shields.io/badge/ERPNext-v16-blue.svg)](https://erpnext.com/)

Ứng dụng bản địa hóa toàn diện và tuân thủ các quy định pháp luật mới nhất của Việt Nam giai đoạn 2025–2026 dành cho hệ sinh thái Frappe & ERPNext v16.

Được fork và tái cấu trúc từ `vietnam_compliance` (`mrhuychien/vietnam_compliance`) theo giấy phép mã nguồn mở GPL-3.0, nâng cấp để đáp ứng trọn vẹn các cải cách pháp lý mang tính bước ngoặt:

1. **Địa giới hành chính 34 tỉnh/thành phố**:
   - Cập nhật chuẩn theo **Nghị quyết số 202/2025/QH15** của Quốc hội (sắp xếp 63 tỉnh/thành xuống 34 đơn vị; kết thúc cấp huyện, thực hiện chính quyền địa phương 2 cấp Tỉnh - Xã).
   - Phân chia vùng lương tối thiểu theo chuẩn **Nghị định 74/2024/NĐ-CP**.

2. **Kế toán & Thuế**:
   - Hệ thống tài khoản chuẩn Thông tư 200/2014/TT-BTC, Thông tư 133/2016/TT-BTC và dự thảo TT99.
   - Bổ sung Tax Template **"VAT Không chịu thuế (Dạy học, Dạy nghề)"** theo khoản 13 Điều 5 **Luật Thuế GTGT 48/2024/QH15** & Nghị định 181/2025/NĐ-CP.
   - Sửa lỗi tương thích chữ ký 3 tham số hàm `get_round_off_accounts` với ERPNext v16.

3. **Hóa đơn điện tử (E-Invoicing)**:
   - Tích hợp cổng HĐĐT đa nhà cung cấp (Viettel, VNPT, FPT, MISA, BKAV).
   - Hỗ trợ linh hoạt cả hai mẫu: **Hóa đơn Bán hàng (02GTTT)** cho lĩnh vực đào tạo/dịch vụ không chịu thuế GTGT và **Hóa đơn GTGT (01GTKT)** cho bán hàng hóa thương mại. Sẵn sàng cho lộ trình **Nghị định 254/2026/NĐ-CP** (hiệu lực 01/07/2026).

4. **Tiền lương & Thuế TNCN**:
   - Cập nhật mức giảm trừ gia cảnh mới theo **Luật số 109/2025/QH15**: Bản thân 15,5 triệu đồng/tháng, người phụ thuộc 6,2 triệu đồng/tháng.
   - Cập nhật lương cơ sở 2,34 triệu đồng/tháng theo **Nghị định 73/2024/NĐ-CP**.
   - Báo cáo bảng lương tháng chuẩn hóa, không dùng raw SQL và tương thích 100% với schema `Salary Slip` của ERPNext v16.

---

## Cài đặt (Installation)

Trong thư mục bench của bạn:

```bash
bench get-app https://github.com/vietdungiitb/vietnam-compliance.git
bench --site [ten-site] install-app vietnam_compliance
bench --site [ten-site] migrate
```

## Giấy phép (License)

GNU General Public License v3.0 (GPL-3.0).
