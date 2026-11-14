# Kết quả: sửa lỗi nav dọc

## Nguyên nhân
1. **Menu bị kẹt trong header (lỗi chính).** Theme mặc định *Siêu anh hùng* và theme *Apple* đặt `backdrop-filter` trên `header`.
   Thuộc tính này biến header thành khung chứa của menu `.nav` (`position:fixed`, nằm trong header), nên menu bị neo vào header
   thay vì màn hình: bị kẹt trong header và gần như biến mất. Theme Cổ điển và Quân sự không bị.
2. **Header không dính khi cuộn.** `html,body{overflow-x:hidden}` biến `body` thành vùng cuộn riêng, nên `position:sticky`
   của header mất tác dụng. Header trôi lên nhưng menu vẫn chừa khoảng trống `--hh` phía trên.

## Đã sửa (`web/index.html`, khối `<style id="mobileFix">`)
- Màn hình >900px: tắt `backdrop-filter`/`filter`/`transform` trên header; hiệu ứng kính mờ chuyển sang `header::before`
  (chỉ cho theme apple và siêu anh hùng). Lớp này không chặn click.
- `overflow-x:hidden` → `overflow-x:clip` (vẫn chặn tràn ngang trên điện thoại; trình duyệt cũ tự dùng lại `hidden`).

## Ai làm gì
- Quản lý: tìm nguyên nhân và sửa.
- claude-3 (review, haiku): xác nhận chẩn đoán, phát hiện thêm lỗi số 2.

## Chưa chắc chắn
- Chưa xem trên trình duyệt thật vì không có quyền chạy Chrome headless. Chủ tải lại trang (Cmd+Shift+R), rồi cuộn trang
  và đổi theme để kiểm tra.
