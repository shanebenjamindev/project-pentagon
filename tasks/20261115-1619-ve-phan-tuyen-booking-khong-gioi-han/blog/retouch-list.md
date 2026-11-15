# Danh sách ảnh cần retouch cho blog/index.html

Xuất vào `blog/images/` đúng tên ở cột 1, định dạng JPG chất lượng cao (`-q:v 2`), cạnh dài 1800px. Hero có thêm bản mobile 4:5. So sánh trước|sau nằm trong `ref/retouch-compare/`.
Trang đã có cơ chế dự phòng: nếu `images/<tên>.jpg` chưa có, trình duyệt tự hiện ảnh gốc trong `pool/` — nên retouch xong chỉ cần thả file vào, không sửa HTML.

Màu thương hiệu để cân tone: navy `#031725`, đỏ rượu `#b20c2b`, trắng ngà `#f5f5f2`. Giữ ánh đèn vàng ấm của quầy, đẩy vùng tối về hướng navy lạnh (không ám vàng/nâu toàn ảnh).

| Ảnh đích | Nguồn | Vị trí trên trang | Gợi ý retouch |
|---|---|---|---|
| `images/hero-quay-bar-den-haag.jpg` (+ `hero-quay-bar-den-haag-mobile.jpg`) | `blog/pool/p13.jpg` | Hero desktop 16:9 và mobile 4:5 | Crop dải dọc khoảng 15–58% ảnh gốc, giữ biển hiệu tròn và ánh đèn hẻm; loại standee phía dưới. Hero được ưu tiên đặt biển phía phải/trên để chừa chỗ nội dung.
| `images/khach-ngoi-quay-bar.jpg` | `blog/pool/v102-b.jpg` | Mục giới thiệu | Khung hình video: giảm noise mạnh, làm nét nhẹ, nâng shadow; crop dọc 4:5 lấy nhóm khách + quầy sáng. Kiểm tra độ phân giải, nếu thấp thì upscale 2x. |
| `images/bartender-pha-che.jpg` | `blog/pool/p30.jpg` | Mục Quyền lợi | Crop dọc 4:5 tập trung bartender + ly; giảm ánh xanh lá trên da, cân bằng trắng ấm nhẹ, tăng tương phản vừa. |
| `images/cocktail-xanh-quay-bar.jpg` | `blog/pool/p32.jpg` | Mục Bảng thưởng | Tăng saturation riêng tông xanh/đỏ của ly, tăng clarity mặt đá quầy, crop 4:5; hạ sáng vùng nền để ly nổi. |
| `images/rot-cocktail-hai-mau.jpg` | `blog/pool/v18-b.jpg` | Mục Ví dụ thu nhập | Khung hình video: giảm noise, làm nét dòng rót, crop 4:5; nếu có frame v18-a/c nét hơn thì dùng frame đó. |
| `images/bartender-tro-chuyen-khach.jpg` | `blog/pool/v63-b.jpg` | Mục Bạn phù hợp | Khung hình video: tăng sáng gương mặt bartender, giảm noise, cân bằng trắng trung tính; crop 4:5 giữ ly xanh ở tiền cảnh. |
| `images/bien-hieu-den-haag-bar.jpg` | `blog/pool/p12.jpg` | Mục Cách ứng tuyển (ghi đè file cũ cùng tên) | Giảm cháy sáng biển tròn (highlight -), nâng shadow cây và standee, giảm noise; crop 4:5 giữ biển + standee. |
| `images/mat-tien-hem-dem.jpg` | `blog/pool/p15.jpg` | Gallery (khung 2:3) | Giảm noise trời đêm, đẩy tone trời về navy, giữ đèn neon đỏ; nâng nhẹ shadow mặt tiền. |
| `images/cocktail-trai-cay.jpg` | `blog/pool/p37.jpg` | Gallery (3:4) | Cân bằng trắng (bớt vàng), tăng sáng ly, làm mờ nhẹ người phía sau nếu cần. |
| `images/whisky-da-quay-bar.jpg` | `blog/pool/p41.jpg` | Gallery (vuông 1:1) | Crop vuông quanh ly + chai, tăng tương phản, làm ấm màu whisky, giảm sáng điều hoà phía sau. |
| `images/menu-signature-cocktail.jpg` | `blog/pool/p35.jpg` | Gallery (4:5) | Làm nét chữ menu, dựng phối cảnh nhẹ, cân bằng trắng trung tính. |
| `images/goc-ngoi-xe-dap-hoa.jpg` | `blog/pool/v83-b.jpg` | Gallery (3:4) | Khung hình video: giảm noise, tăng sáng nhẹ, crop bỏ bớt mép trái; kiểm tra người trong ảnh đồng ý xuất hiện. |
| `images/ruou-black-label-ban-tron.jpg` | `blog/pool/p40.jpg` | Gallery (vuông) | Crop vuông, tăng sáng nền tường, tăng saturation ly xanh, giữ bokeh. |
| `images/bia-goc-bacardi.jpg` | `blog/pool/p27.jpg` | Gallery (4:5) | Tăng sáng tổng thể +0.5EV, giảm noise; có thể xoá gạt tàn/khăn đỏ ở góc trái. |
| `images/ke-ruou-quay-bar.jpg` | `blog/pool/v50-b.jpg` | Gallery (3:4) | Khung hình video: giảm motion blur/làm nét, nâng shadow, cân bằng trắng; dùng frame v50-a/c nếu nét hơn. |

## Thông số brand grade đã áp dụng

Cả 15 ảnh được xuất JPEG `-q:v 2`, cạnh dài 1800px. Grade chung: curves nâng shadow (`0/0.04 0.25/0.33 0.5/0.56 0.75/0.8 1/0.97`), colorbalance split tone (`rs=-0.04:gs=0:bs=0.07:rh=0.05:gh=0.02:bh=-0.04`), saturation `1.2`, unsharp bán kính lớn `13:13:0.35` rồi nét chi tiết `5:5:0.7`, vignette `PI/5`. Giảm noise trước làm nét: ảnh chụp dùng `hqdn3d=2:2:3:3`; frame video dùng `nlmeans=s=3`. Frame nhỏ được upscale Lanczos.

| Nhóm | Ảnh | Crop/xử lý riêng |
|---|---|---|
| Hero | `hero-quay-bar-den-haag` | Nguồn p13, desktop 16:9 từ dải 15–58%; mobile 4:5 không chứa standee. |
| Video | `khach-ngoi-quay-bar`, `rot-cocktail-hai-mau`, `bartender-tro-chuyen-khach`, `goc-ngoi-xe-dap-hoa`, `ke-ruou-quay-bar` | Dùng nlmeans; ảnh dọc 4:5, upscale theo cạnh dài. |
| Ảnh chụp | 9 ảnh còn lại | Dùng hqdn3d; crop 4:5, giữ chủ thể trung tâm. |

Ghi chú:
- Ảnh có người (v102-b, p30, v63-b, v83-b, p32, p37): nên xác nhận với quán là người trong ảnh đồng ý dùng cho quảng cáo tuyển dụng.
- Đã tránh: ảnh trùng lặp nhiều (bộ Black Label p01/p04/p06/p16/p18/p22/p26/p36), ảnh standee "399K unlimited drinks" (p05/p20 — dễ gây nhầm với mức hoa hồng), ảnh tối/mờ (p13, v38-b, v108-b).
- Ảnh cũ trong `images/` (hero-quay-bar-dong-vui, quay-bar-anh-vang, ban-be-quay-bar, menu-cocktail-quay-bar, ly-whisky-quay-bar) không còn được trang dùng.
