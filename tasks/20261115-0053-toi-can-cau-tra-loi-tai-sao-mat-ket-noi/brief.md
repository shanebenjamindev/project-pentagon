# tôi cần câu trả lời tại sao mất kết nối

## Yêu cầu gốc (nguyên văn)

tôi cần câu trả lời tại sao mất kết nối

## Yêu cầu đã tối ưu
- Mục tiêu: tìm nguyên nhân khiến Pentagon báo "mất kết nối" (trên web dashboard `bin/dashboard`).
- Đầu ra mong muốn: câu trả lời ngắn, có nguyên nhân khả dĩ xếp theo mức độ, dẫn chứng từ code, và cách kiểm tra/khắc phục.
- Ràng buộc: chỉ đọc, không sửa code.
- Tiêu chí xong: chỉ ra được đoạn code phát ra thông báo "mất kết nối" và các điều kiện khiến nó xảy ra; nêu rõ điều gì chưa thể xác minh từ log.
- Giả định: "mất kết nối" nghĩa là thông báo "mất kết nối tới bin/dashboard — đang thử lại…" trên web (chủ không nêu rõ, tự giả định hợp lý). Không có log của máy chủ dashboard nên không xác minh được lần mất kết nối cụ thể nào.
