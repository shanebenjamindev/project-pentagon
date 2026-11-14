"""Try to fetch a Drive video's playback stream (for files with download disabled but viewable).
Usage: python3 -I drive_stream.py <file_id> <out_path>
"""
import sys, re, urllib.request, urllib.parse, http.cookiejar

fid, out = sys.argv[1], sys.argv[2]
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]

for url in [f"https://drive.google.com/get_video_info?docid={fid}&drive_originator_app=303",
            f"https://drive.google.com/u/0/get_video_info?docid={fid}"]:
    try:
        body = op.open(url, timeout=30).read().decode("utf-8", "replace")
    except Exception as e:
        print("ERR", url, e); continue
    q = urllib.parse.parse_qs(body)
    print("status:", q.get("status"), q.get("reason"))
    fmt = q.get("fmt_stream_map", [""])[0]
    if not fmt:
        continue
    streams = [s.split("|", 1) for s in fmt.split(",")]
    print("streams:", [s[0] for s in streams])
    best = streams[0][1]
    r = op.open(best, timeout=120)
    n = 0
    with open(out, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b); n += len(b)
    print("OK", n, out)
    sys.exit(0)
sys.exit(1)
