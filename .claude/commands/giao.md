---
description: Giao một task cho đội AI — AI quản lý tối ưu yêu cầu, chia việc, giao cho các AI worker và tổng hợp kết quả
argument-hint: <mô tả task>
---

Chủ vừa giao task sau:

<task>
$ARGUMENTS
</task>

Làm đúng quy trình 6 bước trong CLAUDE.md (tiếp nhận → tối ưu → kế hoạch → giao việc → kiểm tra → tổng hợp):

1. Chạy `bin/workers` để xem worker nào đang dùng được.
2. Chạy `bin/new-task "<tiêu đề ngắn>"`, chép task gốc vào `brief.md`, rồi viết phần "Yêu cầu đã tối ưu".
3. Trình bày ngắn gọn cho chủ: yêu cầu đã tối ưu và kế hoạch chia việc (ai làm gì). Nếu task lớn hoặc mơ hồ,
   chờ chủ đồng ý rồi mới giao. Task nhỏ, rõ ràng thì giao ngay.
4. Giao việc: các việc độc lập thì gọi nhiều agent `worker` cùng lúc. Truyền `-t <thư mục task>` cho mọi lệnh.
5. Kiểm tra từng kết quả, nhờ kiểm tra chéo nếu cần, giao lại nếu chưa đạt.
6. Viết `final.md` và báo cáo cho chủ bằng tiếng Việt.
