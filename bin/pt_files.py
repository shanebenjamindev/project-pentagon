"""File đính kèm (bảng tính, tài liệu) khi giao task / nhắn quản lý.

- decode_files: kiểm tra dữ liệu từ trình duyệt (data URL base64), chỉ nhận các đuôi cho phép.
- save_files: ghi vào <task>/attachments/ và trả đoạn chỉ dẫn để chèn vào yêu cầu gửi quản lý.
  File .xlsx được chuyển thêm ra CSV (mỗi trang tính một file) bằng thư viện chuẩn,
  để nhân viên đọc được ngay mà không cần cài openpyxl/pandas.
"""
import base64
import binascii
import csv
import datetime
import os
import re
import secrets
import zipfile
import xml.etree.ElementTree as ET

MAX_FILES = 5
MAX_FILE_BYTES = 10 * 1024 * 1024
# đuôi cho phép → chữ ký đầu file (None = file chữ, chỉ cần không chứa byte NUL)
ALLOWED = {
    ".csv": None, ".tsv": None, ".txt": None, ".md": None, ".json": None,
    ".xlsx": b"PK\x03\x04", ".docx": b"PK\x03\x04", ".ods": b"PK\x03\x04",
    ".xls": b"\xd0\xcf\x11\xe0", ".pdf": b"%PDF",
}
ACCEPT = ",".join(sorted(ALLOWED))


def safe_name(name):
    base = os.path.basename(str(name or "")).strip()
    stem, ext = os.path.splitext(base)
    stem = re.sub(r"[^\w.\- ]+", "_", stem, flags=re.UNICODE).strip(" .") or "file"
    return stem[:80], ext.lower()


def decode_files(files):
    """Trả danh sách (tên lưu, bytes, tên gốc). Lỗi → ValueError kèm lời nhắn cho chủ."""
    if not files:
        return []
    if not isinstance(files, list) or len(files) > MAX_FILES:
        raise ValueError("Tối đa %d file mỗi lần gửi" % MAX_FILES)
    result = []
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    for index, item in enumerate(files, 1):
        if not isinstance(item, dict):
            raise ValueError("File đính kèm không hợp lệ")
        stem, ext = safe_name(item.get("name"))
        if ext not in ALLOWED:
            raise ValueError("Không nhận file %s — chỉ nhận %s" % (ext or "không đuôi", ", ".join(sorted(ALLOWED))))
        data_url = item.get("data", "")
        if not isinstance(data_url, str) or "," not in data_url or not data_url.startswith("data:"):
            raise ValueError("Dữ liệu file %s%s không hợp lệ" % (stem, ext))
        header, encoded = data_url.split(",", 1)
        if not header.lower().endswith(";base64"):
            raise ValueError("Dữ liệu file %s%s không hợp lệ" % (stem, ext))
        if len(encoded) > MAX_FILE_BYTES * 4 // 3 + 8:
            raise ValueError("File %s%s quá lớn (tối đa 10 MB)" % (stem, ext))
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("Dữ liệu file %s%s không hợp lệ" % (stem, ext))
        if not raw:
            raise ValueError("File %s%s đang trống" % (stem, ext))
        if len(raw) > MAX_FILE_BYTES:
            raise ValueError("File %s%s quá lớn (tối đa 10 MB)" % (stem, ext))
        magic = ALLOWED[ext]
        if magic is None and b"\x00" in raw[:65536] and not raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            raise ValueError("File %s%s không phải file chữ" % (stem, ext))
        if magic is not None and not raw.startswith(magic):
            raise ValueError("Nội dung file %s%s không khớp đuôi file" % (stem, ext))
        saved = "%s-%s-%02d-%s%s" % (stem, stamp, index, secrets.token_hex(2), ext)
        result.append((saved, raw, stem + ext))
    return result


# ---- .xlsx → CSV (chỉ dùng thư viện chuẩn)
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships"}
XLSX_LIMIT = 200 * 1024 * 1024   # tổng dung lượng giải nén tối đa (chống file zip "bom")


def _col_index(ref):
    letters = re.match(r"[A-Z]+", ref or "")
    n = 0
    for ch in letters.group(0) if letters else "A":
        n = n * 26 + ord(ch) - 64
    return n - 1


def _text(node):
    return "".join(t.text or "" for t in node.iter("{%s}t" % NS["m"]))


def xlsx_sheets(path):
    """Trả [(tên trang tính, [hàng...])]. Ngày tháng giữ dạng số sê-ri của Excel."""
    with zipfile.ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist()) > XLSX_LIMIT:
            raise ValueError("file giải nén quá lớn")
        names = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = [_text(si) for si in root.findall("m:si", NS)]
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = {r.get("Id"): r.get("Target") for r in rels.findall("rel:Relationship", NS)}
        out = []
        for sh in wb.findall("m:sheets/m:sheet", NS):
            t = target.get(sh.get("{%s}id" % NS["r"]), "")
            t = t.lstrip("/") if t.startswith("/") else "xl/" + t
            if t not in names:
                continue
            rows = []
            for row in ET.fromstring(z.read(t)).iter("{%s}row" % NS["m"]):
                cells = []
                for c in row.findall("m:c", NS):
                    i = _col_index(c.get("r"))
                    kind = c.get("t")
                    v = c.find("m:v", NS)
                    if kind == "s" and v is not None:
                        val = shared[int(v.text)] if (v.text or "").isdigit() and int(v.text) < len(shared) else ""
                    elif kind == "inlineStr":
                        val = _text(c)
                    else:
                        val = v.text if v is not None and v.text is not None else ""
                    while len(cells) < i:
                        cells.append("")
                    cells.append(val)
                rows.append(cells)
            out.append((sh.get("name") or "Sheet", rows))
        return out


# ---- link Google Sheet / Drive dán trong nội dung task: máy chủ tự lấy (chỉ link đã chia sẻ "Bất kỳ ai có đường liên kết")
SHEET_RE = re.compile(r"https://docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]{20,})[^\s<>\"')\]]*")
DRIVE_RE = re.compile(r"https://drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:export=download&)?id=)([A-Za-z0-9_-]{20,})[^\s<>\"')\]]*")
MAX_LINKS = 3


def _fetch(url):
    """Tải tối đa MAX_FILE_BYTES. Trả (bytes, content-type)."""
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Pentagon)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = r.read(MAX_FILE_BYTES + 1)
        ctype = r.headers.get("Content-Type", "")
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("file trên Drive quá lớn (tối đa 10 MB)")
    return data, ctype


def _guess_ext(raw, ctype, disposition=""):
    if raw.startswith(b"%PDF"):
        return ".pdf"
    if raw.startswith(b"PK\x03\x04"):
        return ".xlsx" if b"xl/" in raw[:4096] or "sheet" in ctype else ".docx" if b"word/" in raw[:4096] else ".zip"
    if raw.startswith(b"\xd0\xcf\x11\xe0"):
        return ".xls"
    head = raw[:2048].lstrip().lower()
    if head.startswith(b"<!doctype html") or head.startswith(b"<html") or "text/html" in ctype:
        return ".html"
    return ".csv" if "csv" in ctype else ".txt"


def fetch_links(text):
    """Tìm link Sheet/Drive trong text, tải về. Trả (danh sách file như decode_files, ghi chú lỗi)."""
    found, notes, seen = [], [], set()
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    links = [("sheet", m.group(1), m.group(0)) for m in SHEET_RE.finditer(text or "")] + \
            [("drive", m.group(1), m.group(0)) for m in DRIVE_RE.finditer(text or "")]
    for kind, fid, link in links:
        if fid in seen:
            continue
        seen.add(fid)
        if len(seen) > MAX_LINKS:
            notes.append("- %s: bỏ qua (tối đa %d link mỗi lần)" % (link, MAX_LINKS))
            continue
        url = ("https://docs.google.com/spreadsheets/d/%s/export?format=xlsx" % fid if kind == "sheet"
               else "https://drive.google.com/uc?export=download&id=%s" % fid)
        try:
            raw, ctype = _fetch(url)
            ext = ".xlsx" if kind == "sheet" and raw.startswith(b"PK\x03\x04") else _guess_ext(raw, ctype)
            if ext == ".html":
                raise ValueError("link chưa chia sẻ công khai (cần bật \"Bất kỳ ai có đường liên kết đều xem được\")")
            if ext not in ALLOWED:
                raise ValueError("loại file %s chưa hỗ trợ" % ext)
            name = ("google-sheet-" if kind == "sheet" else "drive-") + fid[:10]
            found.append(("%s-%s-%s%s" % (name, stamp, secrets.token_hex(2), ext), raw, link))
        except Exception as e:  # mạng lỗi, link riêng tư… — vẫn giao task, chỉ ghi chú cho quản lý
            notes.append("- %s: không đọc được — %s" % (link, getattr(e, "reason", None) or e))
    return found, notes


def save_files(folder, files):
    """Ghi file vào folder (đã kiểm tra nằm trong tasks/). Trả đoạn chỉ dẫn cho quản lý."""
    if not files:
        return ""
    os.makedirs(folder, exist_ok=True)
    lines = []
    for saved, raw, original in files:
        path = os.path.join(folder, os.path.basename(saved))
        with open(path, "xb") as f:
            f.write(raw)
        line = "- %s (từ: %s)" % (path, original)
        if saved.endswith(".xlsx"):
            try:
                csvs = []
                for sheet, rows in xlsx_sheets(path):
                    sname = re.sub(r"[^\w\-]+", "_", sheet, flags=re.UNICODE).strip("_") or "sheet"
                    cp = os.path.splitext(path)[0] + "__" + sname + ".csv"
                    with open(cp, "x", encoding="utf-8", newline="") as f:
                        csv.writer(f).writerows(rows)
                    csvs.append("    - trang tính \"%s\" → %s (%d hàng)" % (sheet, cp, len(rows)))
                if csvs:
                    line += "\n  Đã chuyển sẵn sang CSV (ô ngày tháng là số sê-ri của Excel):\n" + "\n".join(csvs)
            except (zipfile.BadZipFile, KeyError, ET.ParseError, ValueError, OSError) as e:
                line += "\n  (Không tự chuyển sang CSV được: %s)" % e
        lines.append(line)
    return "\n\nFile đính kèm (bảng tính / tài liệu — đọc bằng công cụ Read hoặc python3):\n" + "\n".join(lines)
