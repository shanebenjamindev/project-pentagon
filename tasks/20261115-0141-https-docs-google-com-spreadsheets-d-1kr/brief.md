# Dựng video quảng cáo Summer Breeze theo sheet kịch bản

## Yêu cầu gốc (nguyên văn)

https://docs.google.com/spreadsheets/d/1kRahPaILxE6IGxFZ9kS4I9RSXnJNR1dBC0MauEqD9rs/edit?gid=319163597#gid=319163597

Link Google Sheet/Drive chưa đọc được (báo chủ nếu cần):
- https://docs.google.com/spreadsheets/d/1kRahPaILxE6IGxFZ9kS4I9RSXnJNR1dBC0MauEqD9rs/edit?gid=319163597#gid=319163597: không đọc được — Unauthorized

## Yêu cầu đã tối ưu
- Mục tiêu: CHƯA RÕ — chủ chỉ gửi link Google Sheet, chưa nói cần làm gì với sheet này.
- Đầu ra mong muốn: chưa rõ.
- Ràng buộc: sheet đang ở chế độ riêng tư (xuất CSV trả 401); quyền dùng kết nối Google Drive chưa được cấp trong phiên chạy nền.
- Tiêu chí xong: chưa xác định được.
- Giả định: không tự đoán yêu cầu vì không đọc được nội dung sheet → hỏi chủ.

## Yêu cầu mới (lượt 2)
- Chủ: "tạo video theo sheet".
- Trạng thái: vẫn chưa đọc được sheet (export CSV trả 401, không có file nào được tải lên thư mục task). Kết nối Google Drive đã bị gỡ khỏi cấu hình phiên này nên không đọc được qua connector.
- Cần chủ: (1) dữ liệu sheet dưới dạng .xlsx/.csv tải lên web, hoặc dán nội dung; (2) loại video (ngắn dọc/ngang, độ dài, phong cách, giọng đọc/nhạc, ngôn ngữ); (3) mỗi dòng/cột trong sheet tương ứng cảnh nào.

## Yêu cầu đã tối ưu (lượt 3 — đã có file sheet)
- Nguồn: sheet "FORM YÊU CẦU DỰNG VIDEO" (link gid=714850508), 9 tab: Ceramic Coating Ver 1–6 (đang ẩn), Ver 7, Ver 8, PPF - NewVer (đang hiện).
- Mục tiêu: dựng video quảng cáo trả phí (Paid ads) cho Summer Breeze Ceramic Coating & Mobile Detailing theo đúng kịch bản trong sheet.
- Đầu ra: file MP4 9:16 (1080x1920), 30–60s, mỗi kịch bản 2 bản: VOICE và NO VOICE; phụ đề tiếng Anh; logo ở góc trên suốt video; text on visual theo cột "Text on Visual"; outro logo + (803) 395-8803.
- Phong cách: trẻ trung, năng động; hiệu ứng tuỳ editor; nhạc nền tự chọn (không bản quyền).
- Nguồn hình: thư mục Google Drive trong sheet (logo — công khai, đã kiểm tra), footage xe (Nissan Frontier, Porsche 911, Super Snake, Tesla/BMW/Tundra Ceramic Coat.mov...), stock Pexels. Stock Adobe/Storyblocks không tải được → thay bằng Pexels tương tự.
- Ràng buộc: sheet ghi "Voice Clone" — không có giọng clone của khách → cần chủ chọn cách lồng tiếng.
- Giả định đề xuất: làm trước Ver 8 (mới nhất, có timeline chi tiết 0–38s), sau đó Ver 7 nếu chủ muốn. Bỏ qua các dòng thừa "Brian / Vizion One / $599" ở cuối tab Ver 7/8 (dính từ template khác).
- Tiêu chí xong: video render được, đúng tỉ lệ, đủ cảnh/text/logo/CTA theo sheet, đã review bằng một worker khác.

## Chốt phạm vi (lượt 4) — chủ: "chỉ cần 1 bản ppf"
- Chỉ dựng **1 video** theo tab "PPF - NewVer" (kịch bản đầy đủ trong ppf_script.md): 9:16 1080x1920, ~60s, 8 cảnh, voice AI tiếng Anh (dùng file trong thư mục Voice trên Drive nếu có; nếu không có thì tạo TTS), text trên video tiếng Anh, logo Summer Breeze, CTA cuối "GET YOUR FREE PPF QUOTE TODAY!".
- Video reference nhịp dựng: VizionOne Detail - PPF.mp4. Không tạo footage hư hại/self-healing giả.
- Tiêu chí xong: results/ppf_final.mp4 xem được, đúng thời lượng từng cảnh ±1–2s, đủ text + voice + logo + CTA, đã review chéo.
