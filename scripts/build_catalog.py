#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gravel Bot: turn tutorial HTML files into a smart, searchable learning catalog."""

import datetime
import html
import json
import os
import pathlib
import re
import subprocess
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
TUTORIALS = ROOT / "tutorials"
AUTHOR = "Mehdi Rezghi"
TG_URL = "https://t.me/Mehdirezghi"
COPYRIGHT = f"© {AUTHOR} — {TG_URL}"
SITE_URL = os.environ.get("SITE_URL", "https://mygravel.ir").strip().rstrip("/")
FOOTER_MARK = "gravel-footer"
ANALYTICS_MARK = "gravel-analytics.js"

CATEGORIES = ["شروع هوش مصنوعی", "برنامه‌نویسی", "اتوماسیون", "ابزارهای هوش مصنوعی", "کریپتو و پرداخت", "سایر"]
CATEGORY_RULES = [
    ("شروع هوش مصنوعی", ["نقشه راه", "از کجا شروع", "getting started", "ai roadmap"]),
    ("برنامه‌نویسی", ["python", "پایتون", "javascript", "کدنویسی", "برنامه نویسی", "برنامه‌نویسی", "vscode", "node.js"]),
    ("کریپتو و پرداخت", ["metamask", "متامسک", "کریپتو", "کیف پول", "کیف‌پول", "والت", "تتر", "usdt", "پرداخت"]),
    ("اتوماسیون", ["docker", "داکر", "n8n", "اتوماسیون", "workflow", "ورک فلو", "ورک‌فلو", "powershell", "پاورشل"]),
    ("ابزارهای هوش مصنوعی", ["openclaw", "claude", "کلاد", "chatgpt", "هوش مصنوعی", "ایجنت", "agent", "prompt", "پرامپت"]),
]

TRACK_RULES = [
    ("شروع هوشمند", ["نقشه راه", "از کجا شروع", "getting started", "ai roadmap"]),
    ("OpenClaw", ["openclaw", "اوپن کلا", "اوپن‌کلا"]),
    ("ساخت و اتوماسیون", ["python", "پایتون", "vscode", "node.js", "docker", "داکر", "n8n", "powershell", "پاورشل", "اتوماسیون"]),
    ("ابزارهای حرفه‌ای", ["claude", "کلاد", "cowork", "openrouter", "متامسک", "کیف پول", "کیف‌پول"]),
]

# Curated relations for existing tutorials. New files do not need an entry here: their
# metadata and content are classified automatically.
CURATED = {
    "ai-roadmap-getting-started": {"track": "شروع هوشمند", "sequence": 1, "priority": 100, "featured": True, "category": "شروع هوش مصنوعی", "level": "مبتدی"},
    "install-python-node-vscode(1)": {"track": "ساخت و اتوماسیون", "sequence": 1, "priority": 88, "level": "مبتدی"},
    "python-1hour-vibe-coding": {"track": "ساخت و اتوماسیون", "sequence": 2, "priority": 86, "level": "مبتدی"},
    "powershell": {"track": "ساخت و اتوماسیون", "sequence": 3, "priority": 72},
    "docker-n8n-antigravity": {"track": "ساخت و اتوماسیون", "sequence": 4, "priority": 82, "featured": True},
    "openclaw": {"track": "OpenClaw", "sequence": 1, "priority": 84},
    "openclaw-pro": {"track": "OpenClaw", "sequence": 2, "priority": 78, "featured": True},
    "openrouter-crypto-wallet": {"track": "ابزارهای حرفه‌ای", "sequence": 1, "priority": 66},
    "claude-cowork": {"track": "ابزارهای حرفه‌ای", "sequence": 2, "priority": 74},
    "claude-usage-limit": {"track": "ابزارهای حرفه‌ای", "sequence": 3, "priority": 62},
}

LEGACY = {
    "install-python-node-vscode(1)": {"emoji": "🧰", "category": "برنامه‌نویسی", "time": "حدود ۴۵ دقیقه", "title": "نصب پایتون، Node.js و VS Code", "desc": "جعبه‌ابزار پایه را آماده کن: نصب پایتون، Node.js و VS Code روی ویندوز.", "keywords": "نصب پایتون python node nodejs vscode ویندوز پیش نیاز"},
    "python-1hour-vibe-coding": {"emoji": "🐍", "category": "برنامه‌نویسی", "time": "حدود ۶۰ دقیقه", "title": "پایتون از صفر برای وایب‌کدینگ", "desc": "با کمک هوش مصنوعی اولین برنامه‌ات را از صفر بساز.", "keywords": "پایتون python کدنویسی برنامه نویسی vibe coding"},
    "openrouter-crypto-wallet": {"emoji": "👛", "category": "کریپتو و پرداخت", "time": "حدود ۴۵ دقیقه", "title": "کیف‌پول کریپتو و دسترسی به OpenRouter", "desc": "ساخت کیف‌پول، شارژ امن و دریافت کلید OpenRouter.", "keywords": "متامسک metamask کیف پول کریپتو openrouter api تتر"},
    "docker-n8n-antigravity": {"emoji": "🐳", "category": "اتوماسیون", "time": "حدود ۹۰ دقیقه", "title": "داکر و n8n: خط تولید اتوماسیون هوشمند", "desc": "Docker و n8n را راه بینداز و کارهای تکراری را به گردش‌کارهای هوشمند بسپار.", "keywords": "داکر docker n8n اتوماسیون workflow antigravity"},
    "openclaw": {"emoji": "🦾", "category": "ابزارهای هوش مصنوعی", "time": "حدود ۴۵ دقیقه", "title": "نصب و راه‌اندازی OpenClaw", "desc": "OpenClaw را روی ویندوز راه بینداز و اولین مأموریتش را تعریف کن.", "keywords": "openclaw هوش مصنوعی دستیار cli خط فرمان"},
}


def read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"\s*[|–—-]\s*گراول\s*$", "", value, flags=re.I)
    return re.sub(r"\s+", " ", value).strip()


def visible_text(value):
    value = re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->", " ", value, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", value)


def meta(text, name):
    # Attribute order and single/double quotes are both supported.
    tags = re.findall(r"<meta\b[^>]*>", text, re.I)
    for tag in tags:
        attrs = dict((k.lower(), html.unescape(v)) for k, _, v in re.findall(r"([\w:-]+)\s*=\s*([\"'])(.*?)\2", tag, re.S))
        if attrs.get("name", "").lower() == name.lower():
            return attrs.get("content", "").strip()
    return ""


def title_of(text):
    match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    return clean_text(match.group(1)) if match else ""


def normalize_label(value):
    value = re.sub(r"^[^\w\u0600-\u06ff]+", "", value or "").strip()
    return value if value in CATEGORIES else ""


def haystack(text, stem, title):
    return " ".join([title, stem.replace("-", " "), meta(text, "gravel:keywords"), meta(text, "keywords"), meta(text, "gravel:desc"), meta(text, "description"), visible_text(text)[:6000]]).lower().replace("‌", " ")


def match_rule(hay, rules, fallback):
    for label, keys in rules:
        if any(key in hay for key in keys):
            return label
    return fallback


def infer_level(text, hay):
    explicit = meta(text, "gravel:level").strip()
    if explicit in {"مبتدی", "متوسط", "حرفه‌ای"}:
        return explicit
    if any(x in hay for x in ["حرفه ای", "حرفه‌ای", "پیشرفته", "advanced", "pro"]):
        return "حرفه‌ای"
    if any(x in hay for x in ["از صفر", "مقدماتی", "بدون پیش نیاز", "بدون پیش‌نیاز", "beginner"]):
        return "مبتدی"
    return "متوسط"


def bool_meta(value):
    return (value or "").strip().lower() in {"1", "true", "yes", "بله"}


def int_meta(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def added_date(path):
    try:
        out = subprocess.check_output(["git", "log", "--diff-filter=A", "--follow", "--format=%aI", "-1", "--", str(path.relative_to(ROOT))], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        if out:
            return out.splitlines()[-1][:10]
    except Exception:
        pass
    return datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()


def inject_head(path, text, page_url):
    changed = False
    replacements = {
        "author": AUTHOR,
        "copyright": COPYRIGHT,
    }
    for key, value in replacements.items():
        if not meta(text, key) and "</head>" in text:
            text = text.replace("</head>", f'<meta name="{key}" content="{html.escape(value)}">\n</head>', 1)
            changed = True
    canonical = f'<link rel="canonical" href="{html.escape(page_url)}">'
    if re.search(r'<link\b[^>]*rel=["\']canonical["\'][^>]*>', text, re.I):
        text = re.sub(r'<link\b[^>]*rel=["\']canonical["\'][^>]*>', canonical, text, count=1, flags=re.I)
        changed = True
    elif "</head>" in text:
        text = text.replace("</head>", canonical + "\n</head>", 1)
        changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
    return text


def inject_footer(path, text):
    if FOOTER_MARK in text or "</body>" not in text:
        return text
    footer = f'\n<div class="{FOOTER_MARK}" dir="rtl" style="text-align:center;font-family:Vazirmatn,Tahoma,sans-serif;font-size:13px;opacity:.85;padding:20px 12px;border-top:1px solid rgba(0,0,0,.08)">🏔️ بخشی از <a href="../index.html" style="color:inherit;font-weight:bold">گراول</a> &nbsp;|&nbsp; © {datetime.date.today().year} {AUTHOR} — <a href="{TG_URL}" target="_blank" rel="noopener" style="color:inherit" dir="ltr">@Mehdirezghi</a></div>\n'
    text = text.replace("</body>", footer + "</body>", 1)
    path.write_text(text, encoding="utf-8")
    return text


def inject_analytics(path, text, tutorial_id):
    if ANALYTICS_MARK in text or "</body>" not in text:
        return text
    snippet = f'''\n<script>window.GRAVEL_TUTORIAL_ID={json.dumps(tutorial_id, ensure_ascii=False)};</script>
<script src="../assets/analytics-config.js"></script>
<script src="../assets/gravel-analytics.js"></script>\n'''
    text = text.replace("</body>", snippet + "</body>", 1)
    path.write_text(text, encoding="utf-8")
    return text


def build_catalog():
    items = []
    if not TUTORIALS.exists():
        return items
    for path in sorted(TUTORIALS.glob("*.html")):
        text = read(path)
        page_url = SITE_URL + "/" + urllib.parse.quote("tutorials/" + path.name)
        text = inject_head(path, text, page_url)
        tid = path.stem.replace("-tutorial", "")
        text = inject_footer(path, text)
        text = inject_analytics(path, text, tid)
        legacy = LEGACY.get(tid, {})
        curated = CURATED.get(tid, {})
        title = clean_text(legacy.get("title") or meta(text, "gravel:title") or title_of(text) or path.stem)
        hay = haystack(text, path.stem, title)
        category = curated.get("category") or legacy.get("category") or normalize_label(meta(text, "gravel:category")) or match_rule(hay, CATEGORY_RULES, "سایر")
        track = meta(text, "gravel:track").strip() or curated.get("track") or match_rule(hay, TRACK_RULES, "آموزش‌های مستقل")
        level = curated.get("level") or infer_level(text, hay)
        sequence = int_meta(meta(text, "gravel:sequence"), curated.get("sequence"))
        old_order = int_meta(meta(text, "gravel:order"))
        if sequence is None and old_order is not None:
            sequence = old_order
        priority = int_meta(meta(text, "gravel:priority"), curated.get("priority", 50))
        featured = bool_meta(meta(text, "gravel:featured")) or curated.get("featured", False)
        audience = "شروع از صفر" if level == "مبتدی" else ("توسعه مهارت" if level == "متوسط" else "حرفه‌ای")
        added = added_date(path)
        # Deterministic editorial rank: explicit priority first, then completeness and suitability.
        rank = priority + (8 if featured else 0) + (4 if level == "مبتدی" else 2) + (2 if sequence else 0)
        items.append({
            "id": tid,
            "file": "tutorials/" + path.name,
            "emoji": legacy.get("emoji") or meta(text, "gravel:emoji") or "",
            "title": title,
            "desc": clean_text(legacy.get("desc") or meta(text, "gravel:desc") or meta(text, "description")),
            "time": legacy.get("time") or meta(text, "gravel:time") or "",
            "level": level,
            "audience": audience,
            "category": category,
            "track": track,
            "sequence": sequence,
            "priority": priority,
            "rank": rank,
            "featured": bool(featured),
            "added": added,
            "keywords": legacy.get("keywords") or meta(text, "gravel:keywords") or meta(text, "keywords") or "",
            "prerequisites": meta(text, "gravel:prerequisites"),
        })
    items.sort(key=lambda item: (-item["rank"], item["title"]))
    return items


def update_service_worker(items):
    path = ROOT / "sw.js"
    if not path.exists():
        return
    text = read(path)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    text = re.sub(r'const VERSION = "[^"]*"', f'const VERSION = "{stamp}"', text, count=1)
    offline_files = ["./" + item["file"] for item in items]
    text = re.sub(
        r"const TUTORIALS = \[[^;]*\];",
        "const TUTORIALS = " + json.dumps(offline_files, ensure_ascii=False) + ";",
        text,
        count=1,
        flags=re.S,
    )
    path.write_text(text, encoding="utf-8")


def build_sitemap(items):
    today = datetime.date.today().isoformat()
    records = [(SITE_URL + "/", today), (SITE_URL + "/privacy.html", today)] + [(SITE_URL + "/" + urllib.parse.quote(item["file"]), item["added"] or today) for item in items]
    body = "\n".join(f"  <url><loc>{html.escape(url)}</loc><lastmod>{date}</lastmod></url>" for url, date in records)
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "\n</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")


def main():
    items = build_catalog()
    index = ROOT / "index.html"
    if index.exists():
        inject_head(index, read(index), SITE_URL + "/")
    tracks = {}
    for item in items:
        tracks.setdefault(item["track"], 0)
        tracks[item["track"]] += 1
    catalog = {"name": "گراول", "site": SITE_URL, "copyright": COPYRIGHT, "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "tracks": tracks, "tutorials": items}
    (ROOT / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_service_worker(items)
    build_sitemap(items)
    print(f"Gravel Bot: {len(items)} tutorials, {len(tracks)} learning paths. ✅")


if __name__ == "__main__":
    main()
