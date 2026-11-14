#!/usr/bin/env python3
"""Check local references and remaining links to the original site in site_orig."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re

ROOT = Path(__file__).resolve().parent / "site_orig"
DOMAIN = "detailersmovement.com"
URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)
SRCSET_RE = re.compile(r"(?:^|,)\s*([^,\s]+)(?:\s+[^,]+)?")

class Refs(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if not value: continue
            if key in ("src", "href", "poster", "data-src", "data-lazy-src"):
                self.refs.append((key, value.strip()))
            elif key == "srcset":
                self.refs.extend((key, m.group(1)) for m in SRCSET_RE.finditer(value))
            elif key == "style":
                self.refs.extend(("url()", m.group(2).strip()) for m in URL_RE.finditer(value))
    def handle_data(self, data):
        # CSS embedded in style blocks can include url(...).
        self.refs.extend(("url()", m.group(2).strip()) for m in URL_RE.finditer(data))

def main():
    missing = Counter(); external = Counter(); examples = {}
    pages = sorted(ROOT.rglob("*.html"))
    for page in pages:
        parser = Refs(); parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        for kind, raw in parser.refs:
            parsed = urlsplit(raw)
            if parsed.scheme in ("data", "mailto", "tel", "javascript", "blob") or raw.startswith("#"):
                continue
            if parsed.netloc and DOMAIN in parsed.netloc.lower():
                category = "resource" if kind in ("src", "srcset", "poster", "data-src", "data-lazy-src", "url()") else "page"
                external[category] += 1
                examples.setdefault("external_" + category, raw)
                continue
            if parsed.scheme or parsed.netloc:
                continue
            path = unquote(parsed.path)
            if not path: continue
            target = (page.parent / path) if not path.startswith("/") else (ROOT / path.lstrip("/"))
            if target.is_dir(): target = target / "index.html"
            if not target.exists():
                missing[kind] += 1; examples.setdefault("missing_" + kind, f"{page.relative_to(ROOT)} -> {raw}")
    print(f"HTML pages scanned: {len(pages)}")
    print(f"Missing local references: {sum(missing.values())} {dict(missing)}")
    print(f"Original-domain links: {sum(external.values())} {dict(external)}")
    for key, value in examples.items(): print(f"Example {key}: {value}")

if __name__ == "__main__": main()
