#!/usr/bin/env python3
"""Crawl a whole (public) site: HTML pages + css/js/img/fonts, rewrite everything to local relative paths.
Usage: mirror.py <start_url> <out_dir>
Forms are pointed at a local endpoint (/api/form) served by server.py."""
import os, re, sys, time, hashlib, urllib.request, urllib.error, urllib.parse

START, OUT = sys.argv[1].rstrip("/") + "/", sys.argv[2]
HOST = urllib.parse.urlparse(START).netloc.replace("www.", "")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
EXT_IMG = r"\.(?:png|jpe?g|webp|svg|gif|ico|avif)"
SKIP = ("/wp-json", "/feed", "/wp-admin", "/wp-login", "/xmlrpc", "/wp-content/", "/wp-includes/", "?")
assets = {}
pages = {}  # url -> local rel path (from root)

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return r.read()

def internal(u):
    return urllib.parse.urlparse(u).netloc.replace("www.", "") == HOST

def page_rel(url):
    p = urllib.parse.urlparse(url).path.strip("/")
    return (p + "/index.html") if p else "index.html"

def fetch(url, kind):
    if url in assets:
        return assets[url]
    p = urllib.parse.urlparse(url)
    base, ext = os.path.splitext(os.path.basename(p.path) or "file")
    rel = f"{kind}/{base[:60]}-{hashlib.md5(url.encode()).hexdigest()[:6]}{ext}"
    full = os.path.join(OUT, rel)
    if os.path.exists(full) and os.path.getsize(full) > 0:  # resume: already downloaded
        assets[url] = rel
        return rel
    data, err = None, None
    for i in range(4):
        try:
            data = get(url)
            break
        except urllib.error.HTTPError as e:
            err = e
            if e.code in (404, 403, 410):
                break
            time.sleep(2 * (i + 1))
        except Exception as e:
            err = e
            time.sleep(2 * (i + 1))
    if data is None:
        print("FAIL", url, err)
        assets[url] = None
        return None
    assets[url] = rel
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if kind == "css":
        data = rewrite_css(data.decode("utf-8", "ignore"), url).encode()
    open(full, "wb").write(data)
    return rel

def rewrite_css(txt, base):
    def rep(m):
        u = m.group(2).strip()
        if u.startswith(("data:", "#")):
            return m.group(0)
        full = urllib.parse.urljoin(base, u)
        ext = os.path.splitext(urllib.parse.urlparse(full).path)[1].lower()
        rel = fetch(full, "fonts" if ext in (".woff", ".woff2", ".ttf", ".otf", ".eot") else "img")
        return f"url({m.group(1)}../{rel}{m.group(1)})" if rel else m.group(0)
    return re.sub(r"url\((['\"]?)([^)'\"]+)\1\)", rep, txt)

def links_of(html, base):
    out = []
    for h in re.findall(r'<a\b[^>]*?href=["\']([^"\']+)["\']', html):
        full = urllib.parse.urljoin(base, h.split("#")[0])
        if not full or not internal(full) or any(s in full for s in SKIP):
            continue
        if re.search(r"\.(pdf|zip|png|jpe?g|webp|gif|svg|mp4|xml|txt)$", full, re.I):
            continue
        out.append(full.rstrip("/") + "/")
    return out

def process(url, html):
    depth = page_rel(url).count("/")
    pre = "../" * depth
    def A(rel):
        return pre + rel

    def link_css(m):
        tag = m.group(0)
        h = re.search(r'href=(["\'])([^"\']+)\1', tag)
        if not h or "stylesheet" not in tag:
            return tag
        rel = fetch(urllib.parse.urljoin(url, h.group(2)), "css")
        return tag.replace(h.group(0), f'href="{A(rel)}"') if rel else tag
    html = re.sub(r"<link\b[^>]*>", link_css, html)

    def script_tag(m):
        tag = m.group(0)
        s = re.search(r'src=(["\'])([^"\']+)\1', tag)
        if not s:
            return tag
        full = urllib.parse.urljoin(url, s.group(2))
        if not internal(full):
            return tag
        rel = fetch(full, "js")
        return tag.replace(s.group(0), f'src="{A(rel)}"') if rel else tag
    html = re.sub(r"<script\b[^>]*>", script_tag, html)

    def img_attr(m):
        full = urllib.parse.urljoin(url, m.group(2))
        if not internal(full):
            return m.group(0)
        rel = fetch(full, "img")
        return f'{m.group(1)}"{A(rel)}"' if rel else m.group(0)
    html = re.sub(r'((?:src|data-src|href|data-lazy-src|poster)=)["\']([^"\']+' + EXT_IMG + r'(?:\?[^"\']*)?)["\']', img_attr, html)

    def srcset(m):
        parts = []
        for item in m.group(2).split(","):
            bits = item.strip().split()
            if not bits:
                continue
            full = urllib.parse.urljoin(url, bits[0])
            rel = fetch(full, "img") if internal(full) else None
            parts.append(" ".join([A(rel) if rel else bits[0]] + bits[1:]))
        return f'{m.group(1)}"{", ".join(parts)}"'
    html = re.sub(r'((?:srcset|data-srcset)=)["\']([^"\']+)["\']', srcset, html)

    def style_url(m):
        u = m.group(2)
        if u.startswith(("data:", "#")):
            return m.group(0)
        full = urllib.parse.urljoin(url, u)
        if not internal(full):
            return m.group(0)
        rel = fetch(full, "img")
        return f"url({m.group(1)}{A(rel)}{m.group(1)})" if rel else m.group(0)
    html = re.sub(r"url\((['\"]?)([^)'\"]+)\1\)", style_url, html)

    # internal page links -> local relative
    def a_href(m):
        full = urllib.parse.urljoin(url, m.group(2).split("#")[0])
        frag = "#" + m.group(2).split("#")[1] if "#" in m.group(2) else ""
        key = full.rstrip("/") + "/"
        if key in pages or (internal(full) and not any(s in full for s in SKIP) and not re.search(r"\.\w{2,4}$", full)):
            target = page_rel(key)
            return f'{m.group(1)}"{pre}{target}{frag}"'
        return m.group(0)
    html = re.sub(r'(<a\b[^>]*?href=)["\']([^"\']+)["\']', a_href, html)

    # forms -> local backend
    html = re.sub(r"<form\b([^>]*)>", lambda m: '<form' + re.sub(r'\s(action|method)=("[^"]*"|\'[^\']*\')', "", m.group(1))
                  + ' method="post" action="/api/form" data-local-form="1">', html)
    html = html.replace("</body>", f'<script src="{pre}js/local-form.js"></script></body>', 1)
    return html

# 1) discover pages (BFS)
queue, seen = [START], set()
raw = {}
while queue:
    u = queue.pop(0)
    if u in seen:
        continue
    seen.add(u)
    try:
        raw[u] = get(u).decode("utf-8", "ignore")
    except Exception as e:
        print("PAGE FAIL", u, e)
        continue
    pages[u] = page_rel(u)
    queue += [l for l in links_of(raw[u], u) if l not in seen]
print("pages:", len(pages))

# 2) rewrite + write
os.makedirs(OUT, exist_ok=True)
for u, html in raw.items():
    out = process(u, html)
    path = os.path.join(OUT, pages[u])
    os.makedirs(os.path.dirname(path) or OUT, exist_ok=True)
    open(path, "w", encoding="utf-8").write(out)
    print("page", pages[u])
os.makedirs(os.path.join(OUT, "js"), exist_ok=True)
open(os.path.join(OUT, "js", "local-form.js"), "w").write("""document.addEventListener('submit',function(e){var f=e.target;
if(!f.matches('form[data-local-form]'))return;e.preventDefault();
var d={};new FormData(f).forEach(function(v,k){d[k]=v});d._page=location.pathname;d._form=f.getAttribute('name')||'';
fetch('/api/form',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)})
.then(function(r){return r.json()}).then(function(){f.reset();alert('Thank you! Your message has been sent.')})
.catch(function(){alert('Could not send. Is server.py running?')});},true);""")
print("assets:", len([v for v in assets.values() if v]), "failed:", len([v for v in assets.values() if not v]))
