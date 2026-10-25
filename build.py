#!/usr/bin/env python3
"""Builds the static site from content/ into dist/. No dependencies: python3 build.py"""
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
OUT = ROOT / "dist"

SITE = json.loads((CONTENT / "site.json").read_text(encoding="utf-8"))
FIELDS = json.loads((CONTENT / "fields.json").read_text(encoding="utf-8"))
ITEMS = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((CONTENT / "items").glob("*.json"))]
ITEMS.sort(key=lambda i: i["date"], reverse=True)

LANGS = list(SITE["languages"])
DEFAULT = SITE["defaultLanguage"]
TYPES = {"article": "articles", "book": "books", "paper": "papers"}
FIELD_BY_ID = {f["id"]: f for f in FIELDS}
BASE = SITE.get("baseUrl", "").rstrip("/")
esc = html.escape


def ui(lang, key, **kw):
    s = SITE["ui"][lang].get(key) or SITE["ui"][DEFAULT].get(key, key)
    for k, v in kw.items():
        s = s.replace("{" + k + "}", str(v))
    return s


def tr(obj, lang):
    if not obj:
        return ""
    return obj.get(lang) or obj.get(DEFAULT) or next(iter(obj.values()))


def inline(s):
    s = esc(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    return s


def md(text):
    out = []
    for block in text.strip().split("\n\n"):
        lines = block.split("\n")
        if block.startswith("## "):
            out.append(f"<h2>{inline(block[3:])}</h2>")
        elif all(l.startswith("- ") for l in lines):
            out.append("<ul>" + "".join(f"<li>{inline(l[2:])}</li>" for l in lines) + "</ul>")
        elif block.startswith("> "):
            out.append(f"<blockquote>{inline(block[2:])}</blockquote>")
        else:
            out.append(f"<p>{inline(' '.join(lines))}</p>")
    return "\n".join(out)


def words(text):
    return len(re.findall(r"\w+", text))


def item_path(lang, item):
    return f"{lang}/{TYPES[item['type']]}/{item['id']}.html"


def field_path(lang, fid):
    return f"{lang}/fields/{fid}.html"


def rel(from_path, to_path):
    depth = len(Path(from_path).parts) - 1
    return "../" * depth + to_path


# ---------- pieces ----------

def head(lang, path, title, desc):
    p = lambda t: rel(path, t)
    name = tr(SITE["name"], lang)
    full = title if title == name else f"{title} · {name}"
    alt = ""
    if BASE:
        for l in LANGS:
            alt += f'<link rel="alternate" hreflang="{l}" href="{BASE}/{path.replace(lang + "/", l + "/", 1)}">\n'
        alt += f'<link rel="canonical" href="{BASE}/{path}">\n'
    return f"""<!doctype html>
<html lang="{lang}" dir="{SITE['languages'][lang]['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(full)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:site_name" content="{esc(name)}">
<meta property="og:type" content="website">
{f'<meta property="og:image" content="{BASE}/img/logo-original.jpg">' if BASE else ''}
{alt}<link rel="icon" type="image/png" href="{p('img/favicon.png')}">
<link rel="apple-touch-icon" href="{p('img/apple-touch-icon.png')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@500;600;700&family=Noto+Naskh+Arabic:wght@400;500;600&family=Lexend:wght@500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<link rel="stylesheet" href="{p('css/style.css')}">
</head>
"""


def header(lang, path, active):
    p = lambda t: rel(path, t)
    name = tr(SITE["name"], lang)
    nav = [("home", f"{lang}/index.html"), ("articles", f"{lang}/articles/index.html"),
           ("books", f"{lang}/books/index.html"), ("papers", f"{lang}/papers/index.html"),
           ("about", f"{lang}/about.html"), ("contact", f"{lang}/contact.html")]
    links = "".join(
        f'<a href="{p(u)}"{" aria-current=\"page\"" if k == active else ""}>{esc(ui(lang, "nav_" + k))}</a>'
        for k, u in nav)
    langs = "".join(
        f'<a href="{p(path.replace(lang + "/", l + "/", 1))}" hreflang="{l}" lang="{l}" data-lang="{l}"'
        f'{" aria-current=\"true\"" if l == lang else ""}>{esc(SITE["languages"][l]["label"])}</a>'
        for l in LANGS)
    return f"""<body data-wa="{esc(SITE['whatsapp'])}" data-locale="{SITE['languages'][lang]['locale']}">
<a class="skip" href="#main">{esc(ui(lang, 'skip'))}</a>
<header class="bar">
  <div class="wrap bar-row">
    <a class="brand" href="{p(lang + '/index.html')}">
      <img src="{p('img/emblem.webp')}" alt="" width="64" height="38">
      <span><b>{esc(name)}</b><small>{esc(ui(lang, 'tagline'))}</small></span>
    </a>
    <details class="langs">
      <summary aria-label="{esc(ui(lang, 'language'))}"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 3 2.5 15 0 18M12 3c-2.5 3-2.5 15 0 18"/></svg>{esc(SITE['languages'][lang]['label'])}</summary>
      <div class="langs-menu">{langs}</div>
    </details>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Menu"><span></span><span></span><span></span></button>
  </div>
  <div class="wrap"><nav class="nav" id="site-nav">{links}</nav></div>
</header>
<main id="main">
"""


def footer(lang, path):
    p = lambda t: rel(path, t)
    name = tr(SITE["name"], lang)
    fields = "".join(f'<a href="{p(field_path(lang, f["id"]))}">{esc(tr(f["name"], lang))}</a>' for f in FIELDS)
    sections = "".join(
        f'<a href="{p(f"{lang}/{t}/index.html")}">{esc(ui(lang, "nav_" + t))}</a>' for t in TYPES.values())
    return f"""</main>
<footer class="foot">
  <div class="wrap foot-grid">
    <div class="foot-brand">
      <img src="{p('img/emblem.webp')}" alt="" width="80" height="47">
      <p><b>{esc(name)}</b><br>{esc(ui(lang, 'library_line'))}</p>
    </div>
    <nav><h2>{esc(ui(lang, 'nav_fields'))}</h2>{fields}</nav>
    <nav><h2>{esc(name)}</h2>{sections}<a href="{p(lang + '/about.html')}">{esc(ui(lang, 'nav_about'))}</a><a href="{p(lang + '/contact.html')}">{esc(ui(lang, 'nav_contact'))}</a></nav>
  </div>
  <div class="wrap foot-base">© <span data-year>2026</span> {esc(name)}. {esc(ui(lang, 'footer_rights'))}</div>
</footer>
<a class="fab" href="https://wa.me/{esc(SITE['whatsapp'])}?text={esc(ui(lang, 'wa_text'))}" target="_blank" rel="noopener" aria-label="{esc(ui(lang, 'whatsapp_btn'))}"><svg aria-hidden="true"><use href="#i-wa"/></svg></a>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="i-wa" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2c-1.5 0-3-.4-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.4.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.5.1-.7.3-.2.3-.9.9-.9 2.2s.9 2.5 1 2.7c.1.2 1.8 2.8 4.4 3.9 1.6.7 2.3.8 3.1.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3Z"/></symbol></svg>
<script src="{p('js/site.js')}" defer></script>
</body>
</html>
"""


def page(lang, path, title, desc, active, body):
    write(path, head(lang, path, title, desc) + header(lang, path, active) + body + footer(lang, path))


def write(path, text):
    f = OUT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


def date_tag(d):
    return f'<time datetime="{d}">{d}</time>'


def meta_line(lang, item):
    f = FIELD_BY_ID[item["field"]]
    bits = [f'<span class="chip f-{f["id"]}">{esc(tr(f["name"], lang))}</span>']
    if item["type"] == "book":
        bits.append(f'<span>{esc(tr(item["author"], lang))} · {esc(tr(item["era"], lang))}</span>')
    else:
        bits.append(date_tag(item["date"]))
        if item["type"] == "article":
            body = tr(item.get("body"), lang)
            bits.append(f'<span>{esc(ui(lang, "min_read", n=max(2, round(words(body) / 200))))}</span>')
    return '<div class="meta">' + "".join(bits) + "</div>"


def cover(lang, item, big=False):
    color = item.get("cover", "#1d3a6e")
    return (f'<div class="cover{" big" if big else ""}" style="--c:{color}" aria-hidden="true">'
            f'<span class="cover-t">{esc(tr(item["title"], lang))}</span>'
            f'<span class="cover-a">{esc(tr(item["author"], lang))}</span></div>')


def card(lang, path, item):
    url = rel(path, item_path(lang, item))
    title = esc(tr(item["title"], lang))
    summary = esc(tr(item["summary"], lang))
    search = esc(f'{tr(item["title"], lang)} {tr(item["summary"], lang)} {tr(item.get("author"), lang)}'.lower())
    attrs = f'data-field="{item["field"]}" data-search="{search}"'
    if item["type"] == "book":
        return (f'<article class="card book" {attrs}><a href="{url}">{cover(lang, item)}</a>'
                f'<div><h3><a href="{url}">{title}</a></h3>{meta_line(lang, item)}<p>{summary}</p></div></article>')
    kind = esc(ui(lang, "type_" + item["type"]))
    return (f'<article class="card {item["type"]}" {attrs}><span class="kind">{kind}</span>'
            f'<h3><a href="{url}">{title}</a></h3><p>{summary}</p>{meta_line(lang, item)}</article>')


def filters(lang, items):
    used = [f for f in FIELDS if any(i["field"] == f["id"] for i in items)]
    chips = f'<button type="button" class="fchip" aria-pressed="true" data-filter="all">{esc(ui(lang, "filter_all"))}</button>'
    chips += "".join(
        f'<button type="button" class="fchip" aria-pressed="false" data-filter="{f["id"]}">{esc(tr(f["name"], lang))}</button>'
        for f in used)
    return (f'<div class="filters"><div class="chips" role="group">{chips}</div>'
            f'<input type="search" id="q" placeholder="{esc(ui(lang, "search_placeholder"))}" aria-label="{esc(ui(lang, "search_placeholder"))}"></div>')


# ---------- pages ----------

def build_home(lang):
    path = f"{lang}/index.html"
    p = lambda t: rel(path, t)
    arts = [i for i in ITEMS if i["type"] == "article"]
    books = [i for i in ITEMS if i["type"] == "book"]
    papers = [i for i in ITEMS if i["type"] == "paper"]
    lead = arts[0]
    fields = "".join(
        f'<a class="field f-{f["id"]}" href="{p(field_path(lang, f["id"]))}"><span class="glyph" aria-hidden="true">{f["glyph"]}</span>'
        f'<b>{esc(tr(f["name"], lang))}</b><small>{esc(ui(lang, "items_count", n=sum(i["field"] == f["id"] for i in ITEMS)))}</small></a>'
        for f in FIELDS)

    def section(title, key, items, cls):
        return (f'<section class="sec"><div class="wrap"><div class="sec-head"><h2>{esc(title)}</h2>'
                f'<a href="{p(f"{lang}/{key}/index.html")}">{esc(ui(lang, "view_all"))}</a></div>'
                f'<div class="grid {cls}">{"".join(card(lang, path, i) for i in items)}</div></div></section>')

    body = f"""<section class="hero">
  <div class="wrap hero-grid">
    <div class="hero-text">
      <p class="eyebrow">{esc(ui(lang, 'library_line'))}</p>
      <h1>{esc(ui(lang, 'hero_title'))}</h1>
      <p class="lead">{esc(ui(lang, 'hero_lead'))}</p>
      <div class="actions">
        <a class="btn primary" href="{p(lang + '/articles/index.html')}">{esc(ui(lang, 'cta_articles'))}</a>
        <a class="btn ghost" href="#fields">{esc(ui(lang, 'cta_fields'))}</a>
      </div>
    </div>
    <a class="hero-feature" href="{p(item_path(lang, lead))}">
      <span class="kind">{esc(ui(lang, 'type_article'))}</span>
      <h2>{esc(tr(lead['title'], lang))}</h2>
      <p>{esc(tr(lead['summary'], lang))}</p>
      {meta_line(lang, lead)}
    </a>
  </div>
</section>
<section class="sec" id="fields"><div class="wrap">
  <div class="sec-head"><h2>{esc(ui(lang, 'fields_title'))}</h2></div>
  <p class="sec-lead">{esc(ui(lang, 'fields_lead'))}</p>
  <div class="fields">{fields}</div>
</div></section>
{section(ui(lang, 'latest_articles'), 'articles', arts[1:4] if len(arts) > 3 else arts, 'three')}
{section(ui(lang, 'featured_books'), 'books', books[:4], 'books')}
{section(ui(lang, 'latest_papers'), 'papers', papers[:2], 'two')}
{join_band(lang, path)}
"""
    page(lang, path, tr(SITE["name"], lang), ui(lang, "hero_lead"), "home", body)


def join_band(lang, path):
    return f"""<section class="band"><div class="wrap band-row">
  <div><h2>{esc(ui(lang, 'join_title'))}</h2><p>{esc(ui(lang, 'join_lead'))}</p></div>
  <a class="btn light" href="{rel(path, lang + '/contact.html')}">{esc(ui(lang, 'join_btn'))}</a>
</div></section>"""


def build_listing(lang, type_):
    key = TYPES[type_]
    path = f"{lang}/{key}/index.html"
    items = [i for i in ITEMS if i["type"] == type_]
    cls = {"article": "three", "book": "books", "paper": "two"}[type_]
    body = f"""<section class="page-head"><div class="wrap">
  <h1>{esc(ui(lang, 'nav_' + key))}</h1><p>{esc(ui(lang, key + '_lead'))}</p>
</div></section>
<section class="sec"><div class="wrap">
  {filters(lang, items)}
  <div class="grid {cls}" data-list>{''.join(card(lang, path, i) for i in items)}</div>
  <p class="empty" data-empty hidden>{esc(ui(lang, 'no_results'))}</p>
</div></section>"""
    page(lang, path, ui(lang, "nav_" + key), ui(lang, key + "_lead"), key, body)


def build_field(lang, f):
    path = field_path(lang, f["id"])
    items = [i for i in ITEMS if i["field"] == f["id"]]
    groups = ""
    for t, key in TYPES.items():
        sub = [i for i in items if i["type"] == t]
        if sub:
            cls = {"article": "three", "book": "books", "paper": "two"}[t]
            groups += (f'<section class="sec"><div class="wrap"><div class="sec-head"><h2>{esc(ui(lang, "nav_" + key))}</h2></div>'
                       f'<div class="grid {cls}">{"".join(card(lang, path, i) for i in sub)}</div></div></section>')
    others = "".join(
        f'<a class="fchip" href="{rel(path, field_path(lang, o["id"]))}">{esc(tr(o["name"], lang))}</a>'
        for o in FIELDS if o["id"] != f["id"])
    body = f"""<section class="page-head f-{f['id']}"><div class="wrap">
  <p class="eyebrow">{esc(ui(lang, 'field'))}</p>
  <h1><span class="glyph" aria-hidden="true">{f['glyph']}</span>{esc(tr(f['name'], lang))}</h1>
  <p>{esc(tr(f['description'], lang))}</p>
  <div class="chips">{others}</div>
</div></section>
{groups}"""
    page(lang, path, tr(f["name"], lang), tr(f["description"], lang), "", body)


def build_item(lang, item):
    path = item_path(lang, item)
    p = lambda t: rel(path, t)
    key = TYPES[item["type"]]
    f = FIELD_BY_ID[item["field"]]
    body_src = item.get("body", {})
    if lang in body_src:
        content = f'<div class="prose" lang="{lang}">{md(body_src[lang])}</div>'
    else:
        avail = [l for l in LANGS if l in body_src]
        links = " ".join(
            f'<a href="{p(path.replace(lang + "/", l + "/", 1))}" lang="{l}">{esc(SITE["languages"][l]["label"])}</a>'
            for l in avail)
        content = (f'<div class="prose"><p class="lead">{esc(tr(item["summary"], lang))}</p></div>'
                   f'<p class="notice">{esc(ui(lang, "fallback_notice"))} {links}</p>')
    side = ""
    if item["type"] == "book":
        side = (f'<aside class="side">{cover(lang, item, big=True)}<dl>'
                f'<dt>{esc(ui(lang, "author"))}</dt><dd>{esc(tr(item["author"], lang))}</dd>'
                f'<dt>{esc(ui(lang, "era"))}</dt><dd>{esc(tr(item["era"], lang))}</dd>'
                f'<dt>{esc(ui(lang, "original_language"))}</dt><dd>{esc(SITE["languages"][item["originalLanguage"]]["label"])}</dd>'
                f'<dt>{esc(ui(lang, "field"))}</dt><dd><a href="{p(field_path(lang, f["id"]))}">{esc(tr(f["name"], lang))}</a></dd></dl></aside>')
    elif item["type"] == "paper":
        name = tr(SITE["name"], lang)
        cite = f'{ui(lang, "editorial")}. ({item["date"][:4]}). {tr(item["title"], lang)}. {name}.'
        pdf = f'<a class="btn primary" href="{esc(item["pdf"])}">{esc(ui(lang, "download_pdf"))}</a>' if item.get("pdf") else ""
        side = (f'<aside class="side"><div class="cite"><h2>{esc(ui(lang, "cite"))}</h2><p data-cite>{esc(cite)}</p>'
                f'<button type="button" class="btn ghost small" data-copy data-done="{esc(ui(lang, "copied"))}">{esc(ui(lang, "copy"))}</button></div>{pdf}</aside>')
    related = [i for i in ITEMS if i["field"] == item["field"] and i is not item][:3]
    rel_html = ""
    if related:
        rel_html = (f'<section class="sec related"><div class="wrap"><div class="sec-head"><h2>{esc(ui(lang, "related"))}</h2></div>'
                    f'<div class="grid three">{"".join(card(lang, path, i) for i in related)}</div></div></section>')
    byline = "" if item["type"] == "book" else f'<p class="byline">{esc(ui(lang, "by"))} {esc(tr(item.get("author"), lang) or ui(lang, "editorial"))}</p>'
    body = f"""<article class="item {item['type']}">
  <header class="item-head"><div class="wrap">
    <nav class="crumbs"><a href="{p(lang + '/index.html')}">{esc(ui(lang, 'nav_home'))}</a><span>/</span><a href="{p(f'{lang}/{key}/index.html')}">{esc(ui(lang, 'nav_' + key))}</a><span>/</span><a href="{p(field_path(lang, f['id']))}">{esc(tr(f['name'], lang))}</a></nav>
    <span class="kind">{esc(ui(lang, 'type_' + item['type']))}</span>
    <h1>{esc(tr(item['title'], lang))}</h1>
    {meta_line(lang, item)}
    {byline}
  </div></header>
  <div class="wrap item-body{' with-side' if side else ''}">
    <div>{content}</div>
    {side}
  </div>
</article>
{rel_html}"""
    page(lang, path, tr(item["title"], lang), tr(item["summary"], lang), key, body)


def build_about(lang):
    path = f"{lang}/about.html"
    body = f"""<section class="page-head"><div class="wrap"><h1>{esc(ui(lang, 'about_title'))}</h1></div></section>
<section class="sec"><div class="wrap about">
  <div class="prose">{md(SITE['about'][lang])}</div>
  <img class="about-logo" src="{rel(path, 'img/logo.webp')}" alt="{esc(tr(SITE['name'], lang))}" width="560" height="522">
</div></section>
{join_band(lang, path)}"""
    page(lang, path, ui(lang, "about_title"), ui(lang, "library_line"), "about", body)


def build_contact(lang):
    path = f"{lang}/contact.html"
    msgs = " ".join(f'data-{k.replace("_", "-")}="{esc(ui(lang, k))}"'
                    for k in ["st_missing", "st_sending", "st_ok", "st_err", "st_wa", "st_wa_link"])
    body = f"""<section class="page-head"><div class="wrap"><h1>{esc(ui(lang, 'contact_title'))}</h1><p>{esc(ui(lang, 'contact_lead'))}</p></div></section>
<section class="sec"><div class="wrap contact">
  <div class="contact-side">
    <a class="btn wa" href="https://wa.me/{esc(SITE['whatsapp'])}?text={esc(ui(lang, 'wa_text'))}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-wa"/></svg>{esc(ui(lang, 'whatsapp_btn'))}</a>
    <p class="muted">{esc(ui(lang, 'email_label'))}: <bdi>{esc(SITE['email'])}</bdi></p>
  </div>
  <form id="contact-form" class="form" novalidate data-endpoint="{esc(SITE.get('formEndpoint', ''))}" {msgs}>
    <label for="f-name">{esc(ui(lang, 'form_name'))}<input id="f-name" name="name" required autocomplete="name"></label>
    <label for="f-contact">{esc(ui(lang, 'form_contact'))}<input id="f-contact" name="contact" required></label>
    <label for="f-msg">{esc(ui(lang, 'form_msg'))}<textarea id="f-msg" name="message" required></textarea></label>
    <button class="btn primary" type="submit">{esc(ui(lang, 'form_send'))}</button>
    <p class="status" role="status" id="form-status"></p>
  </form>
</div></section>"""
    page(lang, path, ui(lang, "contact_title"), ui(lang, "contact_lead"), "contact", body)


def build_root():
    langs = "".join(
        f'<a href="{l}/index.html" lang="{l}" hreflang="{l}" data-lang="{l}"><b>{esc(SITE["languages"][l]["label"])}</b>'
        f'<small>{esc(ui(l, "choose_language"))}</small></a>' for l in LANGS)
    name = " · ".join(dict.fromkeys(tr(SITE["name"], l) for l in LANGS))
    write("index.html", f"""<!doctype html>
<html lang="{DEFAULT}" dir="{SITE['languages'][DEFAULT]['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(name)}</title>
<meta name="description" content="{esc(ui(DEFAULT, 'library_line'))}">
<link rel="icon" type="image/png" href="img/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@500;600;700&family=Noto+Naskh+Arabic:wght@400;500;600&family=Lexend:wght@500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<link rel="stylesheet" href="css/style.css">
<script>
(function () {{
  var langs = {json.dumps(LANGS)}, l = null;
  try {{ l = localStorage.getItem("lang"); }} catch (e) {{}}
  if (!l) {{ var n = (navigator.language || "").slice(0, 2); if (langs.indexOf(n) > -1) l = n; }}
  if (l && langs.indexOf(l) > -1) location.replace(l + "/index.html");
}})();
</script>
</head>
<body class="gate">
<main class="gate-box">
  <img src="img/logo.webp" alt="{esc(tr(SITE['name'], DEFAULT))}" width="560" height="522">
  <nav class="gate-langs">{langs}</nav>
</main>
<script src="js/site.js" defer></script>
</body>
</html>
""")


def build_sitemap():
    if not BASE:
        return
    urls = []
    for l in LANGS:
        urls += [f"{l}/index.html", f"{l}/about.html", f"{l}/contact.html"]
        urls += [f"{l}/{t}/index.html" for t in TYPES.values()]
        urls += [field_path(l, f["id"]) for f in FIELDS]
        urls += [item_path(l, i) for i in ITEMS]
    body = "".join(f"<url><loc>{BASE}/{u}</loc></url>" for u in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>')
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)
    build_root()
    for lang in LANGS:
        build_home(lang)
        for t in TYPES:
            build_listing(lang, t)
        for f in FIELDS:
            build_field(lang, f)
        for i in ITEMS:
            build_item(lang, i)
        build_about(lang)
        build_contact(lang)
    build_sitemap()
    print(f"Built {sum(1 for _ in OUT.rglob('*.html'))} pages into {OUT}")


if __name__ == "__main__":
    main()
