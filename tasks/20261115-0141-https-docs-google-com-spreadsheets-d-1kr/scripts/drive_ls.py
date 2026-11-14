"""List (recursively) and optionally download public Google Drive folders/files without gdown.
Usage: python3 -I drive_ls.py ls <folder_id> [depth]
       python3 -I drive_ls.py get <out_dir> <name>=<folder_or_file_id>[:file] ... [--max-mb N]
"""
import sys, os, re, html, json, urllib.request

UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)


def ls(fid):
    h = fetch(f"https://drive.google.com/embeddedfolderview?id={fid}").read().decode("utf-8", "replace")
    out = []
    for kind, i, name in re.findall(
        r'<a href="https://drive.google.com/(file/d|drive/folders)/([^/"?]+)[^"]*"[^>]*>.*?<div class="flip-entry-title">([^<]*)</div>',
        h, re.S):
        out.append(("folder" if "folders" in kind else "file", i, html.unescape(name).strip()))
    return out


def walk(fid, prefix="", depth=3):
    for kind, i, name in ls(fid):
        path = os.path.join(prefix, name)
        if kind == "folder":
            if depth > 0:
                yield from walk(i, path, depth - 1)
        else:
            yield i, path


def download(file_id, dest, max_mb):
    url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
    r = fetch(url, timeout=120)
    size = int(r.headers.get("Content-Length") or 0)
    ctype = r.headers.get("Content-Type", "")
    if "text/html" in ctype:
        return f"SKIP (html, cần quyền hoặc quota): {dest}"
    if size and size > max_mb * 1024 * 1024:
        return f"SKIP (quá lớn {size/1e6:.0f}MB): {dest}"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    n = 0
    with open(dest + ".part", "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
            n += len(b)
            if n > max_mb * 1024 * 1024:
                f.close(); os.remove(dest + ".part")
                return f"SKIP (quá lớn >{max_mb}MB): {dest}"
    os.replace(dest + ".part", dest)
    return f"OK {n/1e6:.1f}MB: {dest}"


def main():
    if sys.argv[1] == "ls":
        depth = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        for i, p in walk(sys.argv[2], "", depth):
            print(i, p)
        return
    out = sys.argv[2]
    max_mb = 800
    args = sys.argv[3:]
    if "--max-mb" in args:
        k = args.index("--max-mb"); max_mb = int(args[k + 1]); del args[k:k + 2]
    for a in args:
        name, ref = a.split("=", 1)
        if ref.endswith(":file"):
            items = [(ref[:-5], name)]
            base = out
        else:
            items = list(walk(ref, "", 2)); base = os.path.join(out, name)
        for i, p in items:
            dest = os.path.join(base, p)
            if os.path.exists(dest):
                print("EXISTS", dest); continue
            try:
                print(download(i, dest, max_mb), flush=True)
            except Exception as e:
                print("ERR", dest, e, flush=True)


if __name__ == "__main__":
    main()
