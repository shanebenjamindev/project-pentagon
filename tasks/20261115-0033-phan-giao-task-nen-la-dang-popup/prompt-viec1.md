Bạn đang sửa dashboard web. Chỉ được sửa file web/index.html (có thể sửa web/*.css nếu thật cần). KHÔNG sửa bin/pt_web.py hay file khác.

YÊU CẦU: Phần "Giao task mới" hiện là một trang riêng (section class="page" data-page="giao", khoảng dòng 569-592; route "/giao" trong parseRoute(); nhánh R.page==="giao" trong route(); nav/title có "giao"; handler #newText/#newGo/#whoPicker/#newMode/#newSplit khoảng dòng 1503-1530). Hãy đổi nó thành POPUP (modal) theo đúng mẫu modal sẵn có (#editModal, #roleModal: class "modal" + "box", mở bằng classList.add("on"), đóng bằng Huỷ/Esc/bấm nền).

Cụ thể:
1. Tạo <div class="modal" id="giaoModal"><div class="box"> ... </div></div> cạnh các modal khác. Bên trong giữ đúng các trường hiện có: tiêu đề "Giao task mới", dòng mô tả, textarea #newText, 3 trường (#whoPicker/#whoBtn/#whoMenu/#whoHint, #newSplit, #newMode), legend rảnh/bận, dòng "Cỡ task..." (#sizeMap), và hàng nút: Huỷ (đóng modal, không còn là link) + nút #newGo "Giao task". Bỏ breadcrumb "Phòng Điều hành" và logo.
2. Nút "+ Giao task" ở thanh trên (<a class="btn pri" href="/giao" data-link>) đổi thành <button class="btn pri" id="giaoOpen">+ Giao task</button>; bấm thì mở modal, gọi renderPicker() và focus #newText.
3. Route "/giao": không còn trang riêng. Trong route(), nếu R.page==="giao" thì mở modal và đổi URL về "/dieu-hanh" bằng history.replaceState, thay vì hiện section. Bỏ section data-page="giao". Sửa title/nav cho gọn.
4. Giao thành công (#newGo onclick): sau khi có d.id, đóng modal, xoá nội dung textarea rồi go(taskUrl(d.id)) như hiện tại. Lỗi: giữ modal mở và hiện toast.
5. Esc đóng modal (thêm vào keydown listener). Bấm nền (e.target===modal) đóng modal. Ctrl/⌘+Enter trong textarea vẫn giao. Nút #newGo disable khi đang gửi.
6. Dùng .modal/.box sẵn có; nếu cần rộng hơn thì style inline như #roleModal (width:min(760px,100%)). Phải chạy được ở giao diện tối và điện thoại (đã có CSS .modal trong mobileFix).
7. Không đổi API /api/giao, không đổi backend.

TIÊU CHÍ: mở popup từ "+ Giao task"; giao được; đóng bằng Huỷ/Esc/bấm nền; /giao mở popup; không còn tham chiếu tới section cũ (grep "giao" và "newText" để kiểm tra). Sau khi sửa, kiểm tra cú pháp JS: tách khối <script> ra file tạm NGOÀI repo (vd /tmp) và chạy node --check nếu có node.

CUỐI CÂU TRẢ LỜI: liệt kê các thay đổi (hàm/dòng) và kết quả kiểm tra cú pháp; ghi rõ nếu không kiểm tra được.
