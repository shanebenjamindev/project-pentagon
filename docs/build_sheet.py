import sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

OUT = sys.argv[1]
FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="1F3A5F")
HEAD_FONT = Font(name=FONT, bold=True, color="FFFFFF", size=10)
BODY_FONT = Font(name=FONT, size=10)
TITLE_FONT = Font(name=FONT, bold=True, size=14, color="1F3A5F")
NOTE_FONT = Font(name=FONT, italic=True, size=9, color="555555")
PHASE_FILLS = {
    "Cài đặt (một lần)": "E8EEF6",
    "Mỗi task": "FFFFFF",
}
LINE = Side(style="thin", color="D0D7E2")
WRAP = Alignment(wrap_text=True, vertical="top")

STATUS_FILL = {
    "Đã xong": "D9EAD3",
    "Cần bạn làm": "FCE5CD",
    "Tự động": "DDE6F5",
    "Đang tắt": "EAD1DC",
    "Chưa bật": "EEEEEE",
    "Đang chạy": "D9EAD3",
    "Đã xử lý": "D9EAD3",
    "Chưa xử lý": "FCE5CD",
}


def table(ws, title, note, headers, rows, widths, status_col=None, status_opts=None):
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws["A2"] = note
    ws["A2"].font = NOTE_FONT
    hr = 4
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=hr, column=c, value=h)
        cell.fill, cell.font = HEAD_FILL, HEAD_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    for r, row in enumerate(rows, hr + 1):
        for c, v in enumerate(row, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font, cell.alignment = BODY_FONT, WRAP
            cell.border = Border(bottom=LINE)
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    ws.freeze_panes = ws.cell(row=hr + 1, column=1)
    ws.sheet_view.showGridLines = False
    last = hr + len(rows)
    if status_col:
        col = chr(64 + status_col)
        dv = DataValidation(type="list", formula1='"' + ",".join(status_opts) + '"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}{hr + 1}:{col}{last + 30}")
        for r in range(hr + 1, last + 1):
            cell = ws[f"{col}{r}"]
            if cell.value in STATUS_FILL:
                cell.fill = PatternFill("solid", fgColor=STATUS_FILL[cell.value])
            cell.alignment = Alignment(vertical="top")
    return last


wb = Workbook()

# 1. Quy trình
ws = wb.active
ws.title = "Quy trình"
steps = [
    ("A1", "Cài đặt (một lần)", "Bạn", "Cài các CLI chính chủ",
     "Claude Code và Codex đã có sẵn. Gemini CLI cài qua Homebrew vì npm không ghi được vào /usr/local/bin.",
     "brew install gemini-cli", "claude 2.1.325, codex 0.160.0, gemini 0.68.0", "Đã xong"),
    ("A2", "Cài đặt (một lần)", "Bạn", "Đăng nhập tài khoản chính",
     "Mỗi CLI đăng nhập bằng gói thuê bao, không cần API key. Claude dùng gói Team, Codex dùng tài khoản ChatGPT.",
     "claude auth login\ncodex login", "claude-main, codex-main: đã đăng nhập", "Đã xong"),
    ("A3", "Cài đặt (một lần)", "Bạn", "Thêm tài khoản phụ",
     "Thêm một dòng vào config/workers.conf (hoặc bỏ dấu # ở dòng mẫu), rồi đăng nhập tài khoản đó. Mỗi tài khoản lưu trong thư mục riêng ~/.pentagon/accounts/<tên>.",
     "bin/login claude-2", "Tài khoản mới hiện trong bin/workers", "Cần bạn làm"),
    ("A4", "Cài đặt (một lần)", "Bạn", "Kiểm tra đội worker",
     "Xem worker nào đã cài CLI, đã đăng nhập và dùng model nào.",
     "bin/workers", "Bảng trạng thái các worker", "Đã xong"),
    ("B1", "Mỗi task", "Bạn", "Giao task",
     "Mở Claude Code trong thư mục Pentagon rồi gõ lệnh /giao kèm mô tả task bằng tiếng Việt.",
     "cd ~/Documents/PERSONAL/Pentagon\nclaude\n/giao <mô tả task>", "Task được AI quản lý tiếp nhận", "Tự động"),
    ("B2", "Mỗi task", "AI quản lý", "Kiểm tra đội",
     "Xem worker nào đang dùng được để chỉ giao việc cho các worker đó.",
     "bin/workers", "Danh sách worker sẵn sàng", "Tự động"),
    ("B3", "Mỗi task", "AI quản lý", "Tiếp nhận task",
     "Tạo thư mục task, chép nguyên văn yêu cầu gốc vào brief.md.",
     "bin/new-task \"<tiêu đề>\"", "tasks/<ngày-giờ>-<tên>/brief.md", "Tự động"),
    ("B4", "Mỗi task", "AI quản lý", "Tối ưu yêu cầu",
     "Viết lại yêu cầu cho rõ: mục tiêu, đầu ra, ràng buộc, tiêu chí xong, giả định. Chỉ hỏi lại bạn khi thiếu thông tin không thể tự giả định.",
     "(AI quản lý tự viết)", "brief.md, mục Yêu cầu đã tối ưu", "Tự động"),
    ("B5", "Mỗi task", "AI quản lý", "Lập kế hoạch",
     "Chia thành việc con, chọn worker theo thế mạnh, đánh dấu việc chạy song song. Task lớn hoặc mơ hồ thì chờ bạn duyệt kế hoạch.",
     "(AI quản lý tự viết)", "plan.md", "Tự động"),
    ("B6", "Mỗi task", "AI quản lý", "Giao việc cho worker",
     "Mỗi việc con giao qua một agent worker, kèm đủ ngữ cảnh vì worker không thấy cuộc trò chuyện. Việc độc lập chạy song song.",
     "bin/ask <worker|claude|codex> -t <thư mục task> \"<việc>\"\nThêm -w -C <thư mục> nếu cho phép sửa file", "Lệnh gửi tới worker", "Tự động"),
    ("B7", "Mỗi task", "bin/ask", "Chọn tài khoản",
     "Gọi theo tên công cụ thì thử từng tài khoản theo thứ tự trong workers.conf. Tài khoản lỗi, hết hạn mức, chưa đăng nhập hoặc quá thời gian thì chuyển sang tài khoản kế tiếp.",
     "(tự động trong bin/ask)", "Dòng OK hoặc FAIL trong log.txt", "Tự động"),
    ("B8", "Mỗi task", "Worker (Claude, Codex, Gemini)", "Làm việc con",
     "Mặc định chỉ được đọc. Có -w thì được sửa file trong thư mục -C. Trả lời bằng tiếng Việt, kết thúc bằng mục Kết quả.",
     "claude -p / codex exec / gemini -p (bin/ask tự gọi)", "results/<worker>-<giờ>.md", "Tự động"),
    ("B9", "Mỗi task", "AI quản lý", "Kiểm tra kết quả",
     "Đọc kết quả từng worker. Việc quan trọng thì nhờ worker khác loại kiểm tra chéo. Chưa đạt thì giao lại kèm nhận xét, tối đa 2 lần, sau đó tự sửa.",
     "bin/ask <worker khác> \"Review ...\"", "Kết quả đã kiểm tra", "Tự động"),
    ("B10", "Mỗi task", "AI quản lý", "Tổng hợp",
     "Viết bản tổng hợp: kết quả chính, ai làm phần nào, phần nào chưa chắc chắn.",
     "(AI quản lý tự viết)", "final.md", "Tự động"),
    ("B11", "Mỗi task", "Bạn", "Nhận và duyệt kết quả",
     "Đọc báo cáo trong Claude Code, mở final.md và results/ để xem chi tiết, giao thêm việc nếu cần.",
     "(đọc final.md)", "Task hoàn tất", "Cần bạn làm"),
]
last = table(
    ws, "Quy trình Pentagon",
    "Một người giao việc, AI quản lý (Claude Code) điều phối các AI worker. Phần A làm một lần, phần B lặp lại cho mỗi task.",
    ["Bước", "Giai đoạn", "Ai làm", "Việc", "Chi tiết", "Lệnh / công cụ", "Đầu ra", "Trạng thái"],
    steps, [7, 16, 18, 22, 52, 38, 30, 14],
    status_col=8, status_opts=["Đã xong", "Cần bạn làm", "Tự động"],
)
for r in range(5, last + 1):
    fill = PHASE_FILLS.get(ws[f"B{r}"].value)
    if fill and fill != "FFFFFF":
        for c in "ABCDEFG":
            ws[f"{c}{r}"].fill = PatternFill("solid", fgColor=fill)
    ws[f"A{r}"].font = Font(name=FONT, size=10, bold=True)

# 2. Worker và tài khoản
ws = wb.create_sheet("Worker và tài khoản")
workers = [
    ("claude-main", "claude", "mặc định (~/.claude)", "mặc định", "Đang chạy", "Lập kế hoạch, review, code khó, viết nội dung", "claude auth login"),
    ("codex-main", "codex", "mặc định (~/.codex)", "gpt-6-luna", "Đang chạy", "Viết và sửa code, refactor, viết test", "codex login"),
    ("gemini-main", "gemini", "mặc định (~/.gemini)", "mặc định", "Đang tắt", "Đọc tài liệu dài, tra cứu, ảnh và video", "bin/login gemini-main"),
    ("claude-2", "claude", "~/.pentagon/accounts/claude-2", "mặc định", "Chưa bật", "Tài khoản Claude thứ 2", "bin/login claude-2"),
    ("claude-3", "claude", "~/.pentagon/accounts/claude-3", "mặc định", "Chưa bật", "Tài khoản Claude thứ 3", "bin/login claude-3"),
    ("codex-2", "codex", "~/.pentagon/accounts/codex-2", "gpt-6-luna", "Chưa bật", "Tài khoản ChatGPT thứ 2", "bin/login codex-2"),
]
table(
    ws, "Worker và tài khoản",
    "Thứ tự dòng trong config/workers.conf là thứ tự ưu tiên khi xoay vòng tài khoản. Sửa file đó để bật hoặc thêm tài khoản.",
    ["Worker", "Công cụ", "Thư mục tài khoản", "Model", "Trạng thái", "Thế mạnh", "Lệnh đăng nhập"],
    workers, [14, 10, 38, 13, 13, 40, 24],
    status_col=5, status_opts=["Đang chạy", "Đang tắt", "Chưa bật"],
)

# 3. Lệnh
ws = wb.create_sheet("Lệnh")
cmds = [
    ("/giao <mô tả>", "Giao task cho AI quản lý, chạy đủ 6 bước", "/giao Viết hàm is_prime kèm test, nhờ AI khác review"),
    ("bin/ask <worker> \"<việc>\"", "Giao việc cho đúng một tài khoản", "bin/ask claude-2 \"Tóm tắt file README\""),
    ("bin/ask <claude|codex|gemini> \"<việc>\"", "Giao việc, tự xoay vòng các tài khoản của công cụ đó", "bin/ask codex \"Viết hàm đọc file CSV\""),
    ("bin/ask ... -w -C <thư mục>", "Cho phép worker sửa file trong thư mục chỉ định", "bin/ask codex -w -C ~/du-an \"Sửa lỗi app.py\""),
    ("bin/ask ... -t <thư mục task>", "Lưu kết quả vào results/ và ghi log.txt", "bin/ask claude -t tasks/20261114-1803-... \"Review code\""),
    ("bin/ask ... -m <model>", "Chọn model cho lần gọi này", "bin/ask codex -m gpt-5.6-terra \"...\""),
    ("bin/ask ... --timeout <giây>", "Giới hạn thời gian mỗi lần thử (mặc định 1200 giây)", "bin/ask claude --timeout 300 \"...\""),
    ("echo \"...\" | bin/ask <worker> -", "Đọc nội dung việc từ stdin, dùng cho prompt dài", "cat yeu-cau.txt | bin/ask claude -"),
    ("bin/workers", "Xem worker, trạng thái đăng nhập, model", "bin/workers"),
    ("bin/login <worker>", "Đăng nhập tài khoản cho một worker", "bin/login claude-2"),
    ("bin/new-task \"<tiêu đề>\"", "Tạo thư mục task với brief.md và plan.md", "bin/new-task \"Viết landing page\""),
]
table(
    ws, "Lệnh",
    "Chạy trong thư mục ~/Documents/PERSONAL/Pentagon.",
    ["Lệnh", "Tác dụng", "Ví dụ"], cmds, [40, 48, 52],
)

# 4. Task mẫu
ws = wb.create_sheet("Task mẫu")
log = [
    ("18:03", "Tiếp nhận, tối ưu, lập kế hoạch", "AI quản lý", None, "Tạo thư mục task, brief.md và plan.md với 3 việc con", "brief.md, plan.md"),
    ("18:04:38", "Viết code và 3 test pytest", "codex-main", 33, "Xong", "results/codex-main-180438.md, code/prime.py, code/test_prime.py"),
    ("18:06:06", "Review code", "claude-main", 80, "Đạt: không có lỗi nghiêm trọng, 3 điểm nên sửa, 6 góp ý nhỏ", "results/claude-main-180606.md"),
    ("18:07", "Sửa theo review và tổng hợp", "AI quản lý", None, "Sửa 3 điểm nên sửa, áp dụng 4 góp ý, bỏ 2 góp ý ngoài yêu cầu", "final.md"),
]
last = table(
    ws, "Task mẫu: hàm is_prime",
    "Task chạy ngày 14/11/2026: viết hàm Python is_prime kèm 3 test pytest, rồi nhờ AI khác review. Pytest chưa chạy thật vì máy chưa cài pytest.",
    ["Thời điểm", "Việc", "Ai làm", "Thời gian worker (giây)", "Kết quả", "File"],
    log, [11, 30, 14, 14, 50, 48],
)
tr = last + 2
ws[f"C{tr}"] = "Tổng thời gian worker"
ws[f"C{tr}"].font = Font(name=FONT, bold=True, size=10)
ws[f"D{tr}"] = f"=SUM(D5:D{last})"
ws[f"D{tr}"].font = Font(name=FONT, bold=True, size=10)

# 5. Sự cố đã gặp
ws = wb.create_sheet("Sự cố đã gặp")
issues = [
    ("Cài Gemini CLI bằng npm báo lỗi EACCES", "/usr/local/bin thuộc quyền root", "Cài bằng Homebrew: brew install gemini-cli", "Đã xử lý"),
    ("Codex báo model gpt-6.1-sol không hỗ trợ", "~/.codex/config.toml đặt model không dùng được với tài khoản ChatGPT", "workers.conf chỉ định gpt-6-luna cho codex-main, không sửa cấu hình chung", "Đã xử lý"),
    ("Gemini báo UNSUPPORTED_CLIENT", "Google ngừng cho Gemini CLI dùng gói miễn phí cá nhân", "Tắt gemini-main. Bật lại khi có Google AI Pro/Ultra hoặc Workspace", "Chưa xử lý"),
    ("Claude hỏi quyền mỗi lần gọi worker", "Chưa có .claude/settings.json cho phép chạy bin/ask", "Tự tạo file theo mẫu ở cuối README.md nếu muốn chạy không cần hỏi", "Chưa xử lý"),
    ("Test pytest của task mẫu chưa chạy", "Máy chưa cài pytest", "pip install pytest rồi chạy python3 -m pytest -q trong thư mục code/ của task", "Chưa xử lý"),
]
table(
    ws, "Sự cố đã gặp",
    "Các lỗi gặp trong lúc dựng hệ thống và cách đã xử lý.",
    ["Vấn đề", "Nguyên nhân", "Cách xử lý", "Trạng thái"],
    issues, [40, 46, 56, 14],
    status_col=4, status_opts=["Đã xử lý", "Chưa xử lý"],
)

wb.save(OUT)
print("saved", OUT)
