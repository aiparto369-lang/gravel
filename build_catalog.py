#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================================
#  ربات گراول (Gravel Bot) — فهرست‌ساز خودکار
#  © Mehdi Rezghi — All rights reserved
#  Telegram: https://t.me/Mehdirezghi
#
#  کار این ربات:
#   1) پوشهٔ tutorials را اسکن می‌کند
#   2) شناسنامهٔ هر آموزش را می‌خواند (متاهای gravel:*) یا حدس می‌زند
#   3) catalog.json را می‌سازد (منبع جست‌وجو و دسته‌بندی سایت)
#   4) امضای © و لینک برگشت به گراول را داخل هر آموزش تزریق می‌کند
#   5) نسخهٔ کش آفلاین (sw.js) را جلو می‌برد
#   6) sitemap.xml و robots.txt را می‌سازد
#  فقط با کتابخانه‌های استاندارد پایتون — بدون هیچ نصب اضافه.
# ==========================================================
import os, re, json, html, subprocess, datetime, pathlib, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
TUTORIALS = ROOT / "tutorials"
AUTHOR = "Mehdi Rezghi"
TG_URL = "https://t.me/Mehdirezghi"
COPYRIGHT = f"© {AUTHOR} — {TG_URL}"
SITE_URL = os.environ.get("SITE_URL", "").strip().rstrip("/")

CATEGORIES = ["برنامه‌نویسی", "کریپتو و پرداخت", "اتوماسیون", "ابزارهای هوش مصنوعی", "سایر"]
HEURISTICS = [
    ("برنامه‌نویسی", ["python", "پایتون", "javascript", "جاوااسکریپت", "کدنویسی", "برنامه‌نویسی", "html", "css", "sql"]),
    ("کریپتو و پرداخت", ["metamask", "متامسک", "کریپتو", "کیف‌پول", "کیف پول", "والت", "نوبیتکس", "تتر", "usdt", "openrouter", "پرداخت", "ارز دیجیتال"]),
    ("اتوماسیون", ["docker", "داکر", "n8n", "اتوماسیون", "ورک‌فلو", "workflow", "زپیر", "zapier"]),
    ("ابزارهای هوش مصنوعی", ["openclaw", "claude", "کلاد", "chatgpt", "هوش مصنوعی", "ایجنت", "agent", "پرامپت", "prompt"]),
]
FOOTER_MARK = "gravel-footer"

# شناسنامهٔ پین‌شدهٔ پنج ایستگاه رزروشدهٔ «مسیر صعود» (قوانین پروژه، بخش ۴).
# کلیدها = id واقعی فایل‌ها (نام فایل منهای ‎-tutorial‎). این مقادیر بر متاهای داخل
# خود فایل مقدم‌اند تا شماره‌گذاری مسیر هرگز به‌هم نریزد. آموزش‌های جدید (شماره ۶ به بعد)
# اینجا نمی‌آیند؛ شناسنامه‌شان از متاهای gravel:* داخل خودشان خوانده می‌شود.
LEGACY = {
    "install-python-node-vscode(1)": {
        "emoji": "🧰", "category": "برنامه‌نویسی", "order": 1, "time": "حدود ۴۵ دقیقه",
        "title": "نصب پایتون، Node.js و VS Code",
        "desc": "جعبه‌ابزار پایه را آماده کن: نصب پایتون، Node.js و VS Code روی ویندوز — پیش‌نیاز همهٔ مسیر.",
        "keywords": "نصب پایتون python node nodejs vscode ویژوال استودیو کد ویندوز پیش‌نیاز"},
    "python-1hour-vibe-coding": {
        "emoji": "🐍", "category": "برنامه‌نویسی", "order": 2, "time": "حدود ۶۰ دقیقه",
        "title": "پایتون از صفر برای وایب‌کدینگ",
        "desc": "اولین قدم دنیای برنامه‌نویسی: پایتون را نصب کن و با کمک هوش مصنوعی اولین برنامه‌ات را بساز.",
        "keywords": "پایتون python نصب کدنویسی برنامه‌نویسی vibe coding"},
    "openrouter-crypto-wallet": {
        "emoji": "👛", "category": "کریپتو و پرداخت", "order": 3, "time": "حدود ۴۵ دقیقه",
        "title": "کیف‌پول کریپتو و دسترسی به OpenRouter",
        "desc": "ساخت کیف‌پول MetaMask، شارژ امن، و گرفتن کلید OpenRouter برای استفاده از مدل‌های هوش مصنوعی.",
        "keywords": "متامسک metamask کیف پول کریپتو نوبیتکس openrouter کلید api تتر"},
    "docker-n8n-antigravity": {
        "emoji": "🐳", "category": "اتوماسیون", "order": 4, "time": "حدود ۹۰ دقیقه",
        "title": "داکر و n8n: خط تولید اتوماسیون هوشمند",
        "desc": "نصب Docker و راه‌اندازی n8n تا کارهای تکراری را به ربات‌های هوشمند بسپاری.",
        "keywords": "داکر docker n8n اتوماسیون ورک‌فلو workflow antigravity"},
    "openclaw": {
        "emoji": "🦾", "category": "ابزارهای هوش مصنوعی", "order": 5, "time": "حدود ۴۵ دقیقه",
        "title": "نصب و راه‌اندازی OpenClaw",
        "desc": "دستیار هوش مصنوعی خط فرمان را روی ویندوز راه بینداز و اولین مأموریتش را بده.",
        "keywords": "openclaw هوش مصنوعی دستیار cli خط فرمان"},
}

def read(p): return p.read_text(encoding="utf-8", errors="replace")

def visible_text(t):
    """فقط متن قابل‌دیدن صفحه — بدون تگ‌ها، اسکریپت و استایل (تا کلمه‌هایی مثل html در کد، دسته‌بندی را گمراه نکنند)."""
    t = re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->", " ", t, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", t)

def meta(text, name):
    m = re.search(r'<meta\s+name=["\']' + re.escape(name) + r'["\']\s+content=["\'](.*?)["\']', text, re.I | re.S)
    return html.unescape(m.group(1).strip()) if m else ""

def title_of(text):
    m = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else ""

def added_date(path):
    """تاریخ اضافه‌شدن فایل از تاریخچهٔ گیت؛ اگر نبود، تاریخ خود فایل."""
    try:
        out = subprocess.check_output(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%aI", "-1", "--", str(path.relative_to(ROOT))],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        if out:
            return out.splitlines()[-1][:10]
    except Exception:
        pass
    return datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()

def categorize(text, stem, title):
    c = meta(text, "gravel:category")
    if c in CATEGORIES:
        return c
    hay = " ".join([
        title, stem.replace("-", " "),
        meta(text, "gravel:keywords"), meta(text, "keywords"),
        meta(text, "gravel:desc"), meta(text, "description"),
        visible_text(text)[:4000],
    ]).lower()
    for cat, keys in HEURISTICS:
        if any(k in hay for k in keys):
            return cat
    return "سایر"

def inject_copyright(path, text):
    """تزریق امضای © و لینک برگشت به گراول در فایل آموزش (فقط اگر نباشد)."""
    changed = False
    if 'name="author"' not in text and "</head>" in text:
        text = text.replace("</head>", f'<meta name="author" content="{AUTHOR}">\n</head>', 1)
        changed = True
    if 'name="copyright"' not in text and "</head>" in text:
        text = text.replace("</head>", f'<meta name="copyright" content="{COPYRIGHT}">\n</head>', 1)
        changed = True
    if FOOTER_MARK not in text and "</body>" in text:
        year = datetime.date.today().year
        footer = (
            f'\n<!-- {COPYRIGHT} -->\n'
            f'<div class="{FOOTER_MARK}" dir="rtl" style="text-align:center;font-family:Vazirmatn,Tahoma,sans-serif;'
            f'font-size:13px;opacity:.85;padding:20px 12px;border-top:1px solid rgba(0,0,0,.08)">'
            f'🏔️ بخشی از <a href="../index.html" style="color:inherit;font-weight:bold">گراول — کتابخانهٔ آموزش گام‌به‌گام</a>'
            f' &nbsp;|&nbsp; © <span dir="ltr">{year} {AUTHOR}</span> — '
            f'<a href="{TG_URL}" target="_blank" rel="noopener" style="color:inherit" dir="ltr">@Mehdirezghi</a>'
            f'</div>\n')
        text = text.replace("</body>", footer + "</body>", 1)
        changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
    return text

def build_catalog():
    items = []
    if not TUTORIALS.exists():
        return items
    for p in sorted(TUTORIALS.glob("*.html")):
        text = read(p)
        text = inject_copyright(p, text)
        tid = p.stem.replace("-tutorial", "")
        legacy = LEGACY.get(tid, {})  # ایستگاه‌های رزروشده: مقادیر پین‌شده مقدم بر متاهای داخل فایل
        title = legacy.get("title") or meta(text, "gravel:title") or title_of(text) or p.stem
        if "order" in legacy:
            order = legacy["order"]
        else:
            order_raw = meta(text, "gravel:order")
            try:
                order = int(order_raw) if order_raw else None
            except ValueError:
                order = None
        cat = legacy.get("category") or meta(text, "gravel:category")
        if cat not in CATEGORIES:
            cat = categorize(text, p.stem, title)
        items.append({
            "id": tid,
            "file": "tutorials/" + p.name,
            "emoji": legacy.get("emoji") or meta(text, "gravel:emoji") or "",
            "title": title,
            "desc": legacy.get("desc") or meta(text, "gravel:desc") or meta(text, "description") or "",
            "time": legacy.get("time") or meta(text, "gravel:time") or "",
            "level": meta(text, "gravel:level") or "مبتدی",
            "category": cat,
            "order": order,
            "added": added_date(p),
            "keywords": legacy.get("keywords") or meta(text, "gravel:keywords") or meta(text, "keywords") or "",
        })
    # مرتب‌سازی: اول مسیر صعود (order)، بعد بقیه بر اساس تاریخ (تازه‌ترها اول)
    items.sort(key=lambda t: (t["order"] is None, t["order"] or 0, t["added"]), reverse=False)
    return items

def bump_sw_version():
    sw = ROOT / "sw.js"
    if not sw.exists():
        return
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    text = read(sw)
    new = re.sub(r'const VERSION = "[^"]*"', f'const VERSION = "{stamp}"', text, count=1)
    if new != text:
        sw.write_text(new, encoding="utf-8")

def build_sitemap(items):
    if not SITE_URL:
        return
    urls = [SITE_URL + "/"] + [SITE_URL + "/" + urllib.parse.quote(t["file"]) for t in items]
    today = datetime.date.today().isoformat()
    body = "\n".join(f"  <url><loc>{html.escape(u)}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<!-- {COPYRIGHT} -->\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "\n</urlset>\n",
        encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        f"# {COPYRIGHT}\nUser-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8")

def main():
    items = build_catalog()
    catalog = {
        "name": "گراول",
        "copyright": COPYRIGHT,
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "tutorials": items,
    }
    (ROOT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    bump_sw_version()
    build_sitemap(items)
    print(f"گراول‌بات: {len(items)} آموزش فهرست شد. ✅")

if __name__ == "__main__":
    main()
