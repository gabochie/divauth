#!/usr/bin/env python3
"""Build the Divine Authority book: print PDF, EPUB, DOCX, and covers."""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown
from lxml import etree, html as LH

# WeasyPrint needs the Pango/GObject native runtime, which is not present on
# every machine that edits this book. Import it only where a PDF is rendered so
# the markdown, EPUB, DOCX and study stages still run without it.
def _weasyprint_html():
    from weasyprint import HTML  # noqa: PLC0415
    return HTML

BOOK_DIR = Path(__file__).resolve().parent
ROOT = BOOK_DIR.parent
OUT = BOOK_DIR / "output"
OUT.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------

def load_config() -> dict:
    with open(BOOK_DIR / "config.json", encoding="utf-8") as fh:
        return json.load(fh)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def num_words(n: int) -> str:
    words = [
        "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
        "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen",
        "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty",
    ]
    return words[n] if 0 <= n < len(words) else str(n)


def roman(n: int) -> str:
    vals = [
        (1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"),
        (90, "xc"), (50, "l"), (40, "xl"), (10, "x"), (9, "ix"),
        (5, "v"), (4, "iv"), (1, "i"),
    ]
    out = []
    for v, s in vals:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


def esc(text: str) -> str:
    return html.escape(text, quote=False)


# --------------------------------------------------------------------------
# Manuscript parsing
# --------------------------------------------------------------------------

TOP_RE = re.compile(r"^# (.+)$", re.MULTILINE)


def parse_manuscript(cfg: dict) -> tuple[str, list[dict]]:
    raw = (BOOK_DIR / cfg["source"]).read_text(encoding="utf-8")
    matches = list(TOP_RE.finditer(raw))
    if not matches:
        raise SystemExit("No top-level headings found in manuscript.")

    preface_body = ""
    first = matches[0]
    first_body = raw[first.end(): matches[1].start()] if len(matches) > 1 else ""
    marker = first_body.find("## About this book")
    if marker >= 0:
        preface_body = first_body[marker:].strip()

    sections = []
    for i, m in enumerate(matches[1:], start=1):
        heading = m.group(1).strip()
        body = raw[m.end(): matches[i + 1].start()].strip() if i + 1 < len(matches) else raw[m.end():].strip()
        body = re.sub(r"\n---\s*$", "", body).strip()
        sections.append(classify(heading, body))

    return preface_body, sections


def classify(heading: str, body: str) -> dict:
    sec = {"heading": heading, "body": body, "type": "section"}

    if heading == "INTRODUCTION":
        sec.update(type="intro", kicker="Introduction", title="Introduction", toc="Introduction")
        return sec

    m = re.match(r"^PART ([IVX]+) — (.+)$", heading)
    if m:
        sec.update(type="part", part=m.group(1), title=m.group(2).strip(),
                   toc=f"Part {m.group(1)} — {m.group(2).strip()}")
        return sec

    if re.match(r"^PART [IVX]+ SUMMARY$", heading):
        part = heading.split()[1]
        sec.update(type="summary", kicker=f"Part {part}", title="Summary",
                   toc=f"Part {part} Summary")
        return sec

    m = re.match(r"^Chapter (\d+) — (.+)$", heading)
    if m:
        n = int(m.group(1))
        sec.update(type="chapter", number=n, kicker=f"Chapter {num_words(n)}",
                   title=m.group(2).strip(), toc=f"{n} · {m.group(2).strip()}",
                   slug=f"ch-{n}")
        return sec

    m = re.match(r"^Appendix ([A-Z]) — (.+)$", heading)
    if m:
        letter = m.group(1)
        sec.update(type="appendix", letter=letter, kicker=f"Appendix {letter}",
                   title=m.group(2).strip(), toc=f"{letter} · {m.group(2).strip()}",
                   slug=f"app-{letter.lower()}")
        return sec

    m = re.match(r"^CONCLUSION — (.+)$", heading)
    if m:
        sec.update(type="conclusion", kicker="Conclusion", title=m.group(1).strip(),
                   toc=f"Conclusion · {m.group(1).strip()}")
        return sec

    sec.update(type="section", kicker="", title=heading.title(),
               toc=heading.title())
    return sec


# --------------------------------------------------------------------------
# Markdown to HTML
# --------------------------------------------------------------------------

CALLOUTS = {"Teaching Notes", "Praxis Notes", "Key Scriptures", "Praxis Checklist"}

LABEL_PREFIXES = (
    "GREEK", "HEBREW", "CENTRAL SCRIPTURE", "PROPOSED ", "KEY TEXTS",
)


def render_body(md_text: str, add_lead: bool = True, context: str = "chapter") -> etree._Element:
    md_text = re.sub(r"^(\s*)- \[ \] ", lambda m: m.group(1) + "- \u2610 ", md_text, flags=re.M)
    md_text = re.sub(r"^(\s*)- \[[xX]\] ", lambda m: m.group(1) + "- \u2611 ", md_text, flags=re.M)

    md = markdown.Markdown(
        extensions=["tables", "sane_lists", "smarty", "md_in_html"],
        output_format="html5",
    )
    body_html = md.convert(md_text)
    root = LH.fragment_fromstring(body_html, create_parent="div")
    root.set("class", "chapter-body")

    # Callouts
    for h3 in list(root.xpath(".//h3")):
        title = h3.text_content().strip()
        if title in CALLOUTS:
            cls = "callout callout-" + slugify(title)
            box = etree.Element("div", {"class": cls})
            h3.addprevious(box)
            box.append(h3)
            nxt = box.getnext()
            while nxt is not None and nxt.tag not in ("h2", "h3", "hr"):
                following = nxt.getnext()
                box.append(nxt)
                nxt = following

    # Labels and run-in heads
    for p in list(root.xpath(".//p")):
        if len(p) != 1 or p[0].tag != "strong":
            continue
        text = p.text_content().strip()
        if not text:
            continue
        if "•" in text or text.upper().startswith(LABEL_PREFIXES):
            p.set("class", "label")
        elif re.match(r"^[1-3]?\s?[A-Z][a-z]+ \d+:\d+", text):
            p.set("class", "label")
        elif text.endswith(":") and len(text) < 80:
            p.set("class", "runin")
        elif text == "Jesus Christ is Lord.":
            p.set("class", "pull")

    # Task list items
    for li in root.xpath(".//li"):
        text = li.text_content().strip()
        if text.startswith(("☐", "☑")):
            li.set("class", "task")

    # Long URLs
    for code in root.xpath(".//code"):
        if (code.text or "").strip().startswith("http"):
            code.set("class", "url")

    # Form block quotes
    for bq in root.xpath(".//blockquote"):
        text = bq.text_content()
        if "____" in text or "☐" in text or "Consent" in text:
            bq.set("class", "form")

    # Table classes
    for table in root.xpath(".//table"):
        table.set("class", "data-table")

    # Section IDs
    used = set()
    for h in root.xpath(".//h2 | .//h3"):
        base = slugify(h.text_content())
        slug = base
        k = 2
        while slug in used:
            slug = f"{base}-{k}"
            k += 1
        used.add(slug)
        h.set("id", slug)

    # Lesson headings
    for h2 in root.xpath(".//h2"):
        title = h2.text_content().strip()
        m = re.match(r"^Lesson (\d+) — (.+)$", title)
        if not m:
            continue
        n = int(m.group(1))
        lesson_title = m.group(2).strip()
        h2.set("class", "lesson")
        h2.set("id", f"lesson-{n}")
        h2.set("data-rh", lesson_title)
        for child in list(h2):
            h2.remove(child)
        h2.text = None
        span = etree.SubElement(h2, "span", {"class": "lesson-kicker"})
        span.text = f"Lesson {num_words(n)}"
        span.tail = lesson_title

    # Strip leading/trailing rules
    for child in list(root):
        if child.tag == "hr":
            root.remove(child)
        else:
            break
    for child in reversed(list(root)):
        if child.tag == "hr":
            root.remove(child)
        else:
            break

    if add_lead:
        candidates = root.xpath(
            ".//p[not(ancestor::blockquote) and not(ancestor::div[contains(@class,'callout')]) "
            "and not(contains(@class,'label')) and not(contains(@class,'runin'))]"
        )
        if candidates:
            p = candidates[0]
            p.set("class", (p.get("class", "") + " lead").strip())
            text = p.text or ""
            if text and text[0].isalpha():
                span = etree.Element("span", {"class": "dropcap"})
                span.text = text[0]
                span.tail = text[1:]
                p.text = None
                p.insert(0, span)

    return root


# --------------------------------------------------------------------------
# HTML assembly
# --------------------------------------------------------------------------

def chapter_header(kicker: str, title: str, data_rh: str, css_class: str = "chapter-title") -> str:
    return (
        f'<header class="chapter-head">'
        f'<p class="chapter-kicker">{esc(kicker)}</p>'
        f'<h1 class="{css_class}" data-rh="{esc(data_rh)}">{esc(title)}</h1>'
        f'<div class="ornament"><span class="diamond"></span></div>'
        f"</header>"
    )


def toc_entry(level: int, label: str, ident: str, kind: str) -> dict:
    return {"level": level, "label": label, "id": ident, "kind": kind}


def build_toc(entries: list[dict], pages: dict | None) -> str:
    rows = []
    for e in entries:
        num = pages.get(e["id"], "") if pages else ""
        rows.append(
            f'<li class="lvl-{e["level"]}">'
            f'<a href="#{e["id"]}"><span class="row">'
            f'<span class="toc-title">{esc(e["label"])}</span>'
            f'<span class="toc-dots"></span>'
            f'<span class="toc-page">{num}</span>'
            f"</span></a></li>"
        )
    return "\n".join(rows)


def build_front_matter(cfg: dict, preface_html: str, entries: list[dict], pages: dict | None) -> str:
    title = esc(cfg["title"])
    subtitle = esc(cfg["subtitle"])
    subtitle2 = esc(cfg["subtitle2"])
    desc = esc(cfg["description"])
    author = esc(cfg["author"])
    publisher = esc(cfg["publisher"])
    year = cfg["year"]
    edition = esc(cfg["edition"])

    return f"""
<section class="half-title">
  <div class="ht-title">{title.upper()}</div>
  <div class="ht-rule"></div>
</section>

<section class="front-blank"></section>

<section class="title-page">
  <div class="tp-kicker">Biblical Teaching · Christology · Spiritual Authority</div>
  <h1 class="tp-title">{title.upper()}</h1>
  <div class="tp-rule"></div>
  <div class="tp-sub">{subtitle}</div>
  <div class="tp-sub2">{subtitle2}</div>
  <div class="tp-desc">{desc}</div>
  <div class="tp-author">{author.upper()}</div>
  <div class="tp-imprint">{publisher}</div>
</section>

<section class="copyright">
  <p class="cr-title">{title}: {subtitle}</p>
  <p>Copyright © {year} {cfg.get('copyright_holder', author)}. All rights reserved.</p>
  <p>{edition}.</p>
  <p>No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other non-commercial uses permitted by copyright law.</p>
  <p>Unless otherwise noted, Scripture quotations are from the Authorized (King James) Version, which is in the public domain. Original-language terms are transliterated and, where useful, given in Greek or Hebrew script.</p>
  <p>This book is a theological and pastoral resource. It is not a substitute for medical care, psychiatric care, counselling, or emergency services. Where there is risk of harm, medical or emergency care should be sought immediately.</p>
  <p>Cover and interior design by {publisher}. Set in EB Garamond, Cormorant Garamond, Cinzel, and Inter.</p>
  <p class="cr-small">Published by {publisher}.</p>
  {f'<p class="cr-small">ISBN: {esc(cfg["isbn"])}</p>' if cfg.get("isbn") else ''}
</section>

<section class="epigraph">
  <div class="ep-mark"><span class="diamond diamond-lg"></span></div>
  <div class="ep-text">“Jesus Christ is not merely more powerful than demons. He is Lord over the entire spiritual order.”</div>
  <div class="ep-cite">The Governing Thesis</div>
</section>

<section class="front-blank"></section>

<section class="toc" id="toc">
  <h1>Contents</h1>
  <div class="toc-rule"></div>
  <ol>
    {build_toc(entries, pages)}
  </ol>
</section>

<section class="front-section" id="preface">
  <header class="chapter-head">
    <p class="chapter-kicker">Before You Begin</p>
    <h1 class="chapter-title" data-rh="Preface">Preface</h1>
    <div class="ornament"><span class="diamond"></span></div>
  </header>
  {preface_html}
</section>
"""


def build_main(cfg: dict, sections: list[dict], spacer: bool) -> tuple[str, list[dict], list[dict]]:
    chunks: list[str] = []
    entries: list[dict] = []
    epub_sections: list[dict] = []

    spacer_html = '<section class="front-spacer"></section>' if spacer else ""

    for sec in sections:
        typ = sec["type"]

        if typ == "part":
            pid = f"part-{sec['part'].lower()}"
            entries.append(toc_entry(0, sec["toc"], pid, "main"))
            chunks.append(
                f'<section class="part-page" id="{pid}">'
                f'<p class="part-kicker">Part {sec["part"]}</p>'
                f'<div class="part-rule"></div>'
                f'<h1 class="part-title">{esc(sec["title"])}</h1>'
                f'<div class="part-orn"><span class="diamond"></span></div>'
                f"</section>"
            )
            epub_sections.append({
                "id": pid,
                "title": f"Part {sec['part']} — {sec['title']}",
                "html": f'<h1 class="part-title">{esc(sec["title"])}</h1>',
            })
            if sec["body"].strip():
                body_el = render_body(sec["body"], add_lead=False, context="part")
                body_html = LH.tostring(body_el, encoding="unicode", method="html")
                # Collect lesson TOC entries
                for h2 in body_el.xpath(".//h2[contains(@class,'lesson')]"):
                    lid = h2.get("id")
                    title = h2.get("data-rh")
                    n = int(re.search(r"(\d+)", lid).group(1))
                    entries.append(toc_entry(1, f"Lesson {n} · {title}", lid, "main"))
                chunks.append(
                    f'<section class="part-body" id="{pid}-body">'
                    f'<div class="rh-seed">Part {sec["part"]}</div>'
                    f"{body_html}</section>"
                )
                intro_md = re.split(r"\n## Lesson \d+ — ", sec["body"])[0]
                intro_el = render_body(intro_md, add_lead=False, context="part")
                epub_sections.append({
                    "id": f"{pid}-intro",
                    "title": f"Part {sec['part']} — Introduction",
                    "html": LH.tostring(intro_el, encoding="unicode", method="html"),
                })
                # Split lessons for EPUB
                for lesson in body_el.xpath(".//h2[contains(@class,'lesson')]"):
                    lid = lesson.get("id")
                    lesson_title = lesson.get("data-rh") or lid
                    parts = []
                    sib = lesson.getnext()
                    while sib is not None and sib.tag != "h2":
                        parts.append(LH.tostring(sib, encoding="unicode", method="html"))
                        sib = sib.getnext()
                    epub_sections.append({
                        "id": lid,
                        "title": lesson_title,
                        "html": f'<h1 class="chapter-title">{esc(lesson_title)}</h1>' + "".join(parts),
                    })
            continue

        if typ == "chapter":
            sid = sec["slug"]
            entries.append(toc_entry(1, sec["toc"], sid, "main"))
            body_el = render_body(sec["body"], add_lead=True, context="chapter")
            body_html = LH.tostring(body_el, encoding="unicode", method="html")
            chunks.append(
                f'<section class="chapter" id="{sid}">'
                f'{chapter_header(sec["kicker"], sec["title"], sec["title"])}'
                f"{body_html}</section>"
            )
            epub_sections.append({
                "id": sid,
                "title": f"{sec['number']}. {sec['title']}",
                "html": f'<h1 class="chapter-title"><span class="ch-num">{esc(sec["kicker"])}</span>{esc(sec["title"])}</h1>' + re.sub(r'<div class="chapter-body">|</div>$', '', body_html),
            })
            continue

        if typ == "appendix":
            sid = sec["slug"]
            entries.append(toc_entry(1, sec["toc"], sid, "main"))
            body_el = render_body(sec["body"], add_lead=False, context="appendix")
            body_html = LH.tostring(body_el, encoding="unicode", method="html")
            chunks.append(
                f'<section class="appendix" id="{sid}">'
                f'{chapter_header(sec["kicker"], sec["title"], sec["title"])}'
                f"{body_html}</section>"
            )
            epub_sections.append({
                "id": sid,
                "title": f"Appendix {sec['letter']} — {sec['title']}",
                "html": f'<h1 class="chapter-title"><span class="ch-num">Appendix {esc(sec["letter"])}</span>{esc(sec["title"])}</h1>' + re.sub(r'<div class="chapter-body">|</div>$', '', body_html),
            })
            continue

        # intro / conclusion / summary / generic section
        if typ == "intro":
            sid = "intro"
        elif typ == "conclusion":
            sid = "conclusion"
        elif typ == "summary":
            bits = sec["kicker"].split()
            # A part summary must be unique: books can have several of them.
            sid = f"part-{bits[1].lower()}-summary" if len(bits) > 1 else "summary"
        else:
            sid = slugify(sec["heading"])
        entries.append(toc_entry(0, sec["toc"], sid, "main"))
        body_el = render_body(sec["body"], add_lead=True, context=typ)
        body_html = LH.tostring(body_el, encoding="unicode", method="html")
        main_start = " main-start" if typ == "intro" else ""
        chunks.append(
            f'<section class="chapter{main_start}" id="{sid}">'
            f'{chapter_header(sec["kicker"], sec["title"], sec["title"])}'
            f"{body_html}</section>"
        )
        epub_sections.append({
            "id": sid,
            "title": sec["toc"],
            "html": f'<h1 class="chapter-title">{esc(sec["title"])}</h1>' + re.sub(r'<div class="chapter-body">|</div>$', '', body_html),
        })

    return spacer_html + "\n".join(chunks), entries, epub_sections


def build_html(cfg: dict, preface_html: str, main_html: str, entries: list[dict],
               pages: dict | None, extra_head: str = "") -> str:
    front = build_front_matter(cfg, preface_html, entries, pages)
    title = esc(cfg["title"])
    author = esc(cfg["author"])
    desc = esc(cfg["description"])
    return f"""<!DOCTYPE html>
<html lang="{cfg['language']}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="author" content="{author}">
<meta name="description" content="{desc}">
<meta name="keywords" content="Jesus Christ, authority, deliverance, demons, unclean spirits, spiritual warfare, biblical teaching, Christology">
<meta name="generator" content="{esc(cfg.get('generator', 'Divine Authority book build'))}">
<link rel="stylesheet" href="styles/print.css">
{extra_head}
</head>
<body>
{front}
<main>
{main_html}
</main>
</body>
</html>
"""


# --------------------------------------------------------------------------
# PDF build
# --------------------------------------------------------------------------

def build_pdf(cfg: dict, preface_body: str, sections: list[dict]) -> tuple[Path, int, list[dict]]:
    preface_el = render_body(preface_body, add_lead=False, context="preface")
    preface_html = LH.tostring(preface_el, encoding="unicode", method="html")

    spacer = False
    doc = None
    anchors: dict[str, int] = {}
    entries: list[dict] = []

    for _ in range(4):
        main_html, entries, epub_sections = build_main(cfg, sections, spacer)
        entries = [toc_entry(0, "Preface", "preface", "front")] + entries
        html_str = build_html(cfg, preface_html, main_html, entries, None)
        doc = _weasyprint_html()(string=html_str, base_url=str(BOOK_DIR)).render()
        anchors = {}
        for i, page in enumerate(doc.pages):
            for a in page.anchors:
                anchors.setdefault(a, i)
        intro_i = anchors.get("intro", 0)
        if intro_i % 2 == 1 and not spacer:
            spacer = True
            continue
        break

    intro_i = anchors.get("intro", 0)
    pages: dict[str, str] = {}
    for e in entries:
        i = anchors.get(e["id"])
        if i is None:
            continue
        if e["kind"] == "front":
            pages[e["id"]] = roman(i + 1)
        else:
            pages[e["id"]] = str(i - intro_i + 1)

    main_html, entries, epub_sections = build_main(cfg, sections, spacer)
    entries = [toc_entry(0, "Preface", "preface", "front")] + entries
    html_str = build_html(cfg, preface_html, main_html, entries, pages)
    (OUT / "interior.html").write_text(html_str, encoding="utf-8")
    doc = _weasyprint_html()(string=html_str, base_url=str(BOOK_DIR)).render()
    pdf_path = OUT / "Divine_Authority_Interior_6x9.pdf"
    doc.write_pdf(str(pdf_path))

    # Persist the EPUB source for the next stage
    (OUT / "epub_sections.json").write_text(
        json.dumps(epub_sections, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "preface.html").write_text(preface_html, encoding="utf-8")

    return pdf_path, len(doc.pages), entries


# --------------------------------------------------------------------------
# Covers
# --------------------------------------------------------------------------

def cover_css(cfg: dict) -> str:
    return """
@font-face { font-family: "Cinzel"; src: url("assets/fonts/cinzel-400-normal.ttf"); font-weight: 400; }
@font-face { font-family: "Cinzel"; src: url("assets/fonts/cinzel-600-normal.ttf"); font-weight: 600; }
@font-face { font-family: "Cinzel"; src: url("assets/fonts/cinzel-700-normal.ttf"); font-weight: 700; }
@font-face { font-family: "Cormorant Garamond"; src: url("assets/fonts/cormorant-garamond-400-normal.ttf"); font-weight: 400; }
@font-face { font-family: "Cormorant Garamond"; src: url("assets/fonts/cormorant-garamond-600-normal.ttf"); font-weight: 600; }
@font-face { font-family: "Cormorant Garamond"; src: url("assets/fonts/cormorant-garamond-600-italic.ttf"); font-weight: 600; font-style: italic; }
@font-face { font-family: "Inter"; src: url("assets/fonts/inter-400-normal.ttf"); font-weight: 400; }
@font-face { font-family: "Inter"; src: url("assets/fonts/inter-600-normal.ttf"); font-weight: 600; }

@page { size: 6in 9in; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { font-family: "Cormorant Garamond", serif; }
.cover {
  position: relative; width: 6in; height: 9in; overflow: hidden;
  background: #0a1420;
  background-image:
    radial-gradient(circle at 50% 18%, rgba(201,178,122,0.22) 0%, rgba(201,178,122,0.05) 26%, rgba(10,20,32,0) 52%),
    linear-gradient(180deg, #0d1a29 0%, #0a1420 55%, #07101a 100%);
  color: #e9e1d0;
}
.cover .frame {
  position: absolute; top: 0.34in; left: 0.34in; right: 0.34in; bottom: 0.34in;
  border: 0.7pt solid rgba(201,178,122,0.55);
}
.cover .frame-inner {
  position: absolute; top: 0.39in; left: 0.39in; right: 0.39in; bottom: 0.39in;
  border: 0.35pt solid rgba(201,178,122,0.3);
}
.cover .content {
  position: absolute; top: 0.9in; left: 0.55in; right: 0.55in;
  text-align: center;
}
.cover .topline {
  font-family: "Inter"; font-size: 6.4pt; font-weight: 600;
  letter-spacing: 0.28em; color: #b9a878; text-transform: uppercase;
}
.cover .cross {
  font-family: "Cormorant Garamond"; font-size: 15pt; color: #c9b27a;
  margin-top: 0.34in; line-height: 1;
}
.cover h1 {
  font-family: "Cinzel"; font-weight: 700; font-size: 49pt; line-height: 1.02;
  letter-spacing: 0.055em; color: #d9b96b; margin: 0.26in 0 0;
}
.cover h1 span { display: block; }
.cover .rule {
  width: 1.25in; border-top: 0.8pt solid #c9b27a; margin: 0.24in auto 0.2in;
}
.cover .sub {
  font-family: "Cormorant Garamond"; font-weight: 600; font-size: 18.5pt;
  line-height: 1.18; color: #efe7d6;
}
.cover .sub2 {
  font-family: "Cormorant Garamond"; font-style: italic; font-weight: 600;
  font-size: 12.5pt; color: #c7bda8; margin-top: 0.06in;
}
.cover .desc {
  font-family: "Inter"; font-size: 6.3pt; font-weight: 400; letter-spacing: 0.14em;
  text-transform: uppercase; color: #9d957f; line-height: 1.7;
  margin: 0.34in auto 0; max-width: 4.1in;
}
.cover .author {
  position: absolute; left: 0.55in; right: 0.55in; bottom: 0.72in;
  text-align: center;
  font-family: "Cinzel"; font-weight: 600; font-size: 13pt;
  letter-spacing: 0.3em; color: #d9b96b;
}
.cover .imprint {
  position: absolute; left: 0.55in; right: 0.55in; bottom: 0.48in;
  text-align: center;
  font-family: "Inter"; font-size: 5.8pt; letter-spacing: 0.2em;
  text-transform: uppercase; color: #7e7664;
}
"""


def build_cover_front(cfg: dict) -> tuple[Path, Path]:
    html_str = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{cover_css(cfg)}</style></head>
<body><div class="cover">
  <div class="frame"></div><div class="frame-inner"></div>
  <div class="content">
    <div class="topline">Biblical Teaching · Christology · Spiritual Authority</div>
    <div class="cross"><span class="diamond"></span></div>
    <h1><span>DIVINE</span><span>AUTHORITY</span></h1>
    <div class="rule"></div>
    <div class="sub">Christ, Demons and Unclean Spirits</div>
    <div class="sub2">His Authority and Power Over Them</div>
    <div class="desc">A Christ-Centred Teaching Book and Practical Handbook for Deliverance Ministry</div>
  </div>
  <div class="author">{esc(cfg['author']).upper()}</div>
  <div class="imprint">{esc(cfg['publisher'])}</div>
</div></body></html>"""
    pdf = OUT / "Divine_Authority_Cover_Front.pdf"
    _weasyprint_html()(string=html_str, base_url=str(BOOK_DIR)).write_pdf(str(pdf))
    png = OUT / "cover.jpg"
    subprocess.run(
        ["pdftoppm", "-jpeg", "-r", "300", "-singlefile", str(pdf), str(OUT / "cover")],
        check=True,
    )
    # pdftoppm names the file cover.jpg when -jpeg and -singlefile
    return pdf, png


def build_cover_wrap(cfg: dict, page_count: int) -> Path:
    spine = max(0.25, page_count * cfg["spine_per_page_in"])
    bleed = cfg["bleed_in"]
    width = 6 + 6 + spine + 2 * bleed
    height = 9 + 2 * bleed

    html_str = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{cover_css(cfg)}
@page {{ size: {width:.4f}in {height:.4f}in; margin: 0; }}
body {{ width: {width:.4f}in; height: {height:.4f}in; background: #0a1420; }}
.panel {{ position: absolute; top: {bleed}in; width: 6in; height: 9in; }}
.back {{ left: {bleed}in; }}
.spine {{ left: {bleed + 6:.4f}in; width: {spine:.4f}in; height: 9in; top: {bleed}in; }}
.front {{ left: {bleed + 6 + spine:.4f}in; }}
.back, .spine, .front {{ overflow: hidden; }}
.back {{ background: #0a1420; background-image: linear-gradient(180deg,#0d1a29 0%,#0a1420 60%,#07101a 100%); }}
.spine {{ background: #0a1420; border-left: 0.4pt solid rgba(201,178,122,0.28); border-right: 0.4pt solid rgba(201,178,122,0.28); }}
.back .inner, .front .inner {{ position: absolute; top: 0; left: 0; right: 0; bottom: 0; }}
.back .frame, .front .frame {{ position: absolute; top: 0.34in; left: 0.34in; right: 0.34in; bottom: 0.34in; border: 0.7pt solid rgba(201,178,122,0.55); }}
.back .frame-inner, .front .frame-inner {{ position: absolute; top: 0.39in; left: 0.39in; right: 0.39in; bottom: 0.39in; border: 0.35pt solid rgba(201,178,122,0.3); }}
.back .content {{ position: absolute; top: 0.78in; left: 0.58in; right: 0.58in; color: #e9e1d0; }}
.back .kicker {{ font-family: "Inter"; font-size: 6.2pt; font-weight: 600; letter-spacing: 0.24em; text-transform: uppercase; color: #b9a878; }}
.back .headline {{ font-family: "Cormorant Garamond"; font-weight: 600; font-size: 20pt; line-height: 1.18; color: #efe7d6; margin-top: 0.18in; }}
.back .blurb {{ font-family: "EB Garamond", serif; font-size: 9.2pt; line-height: 1.5; color: #d8d0bf; margin-top: 0.16in; }}
.back .blurb p {{ margin: 0 0 6pt; text-indent: 0; }}
.back .bullets {{ margin-top: 0.16in; }}
.back .bullets div {{ font-family: "Inter"; font-size: 7.2pt; line-height: 1.55; color: #cfc6b3; margin: 0 0 3pt; }}
.back .bullets b {{ color: #d9b96b; font-weight: 600; }}
.back .author {{ position: absolute; left: 0.58in; right: 0.58in; bottom: 0.86in; font-family: "Cinzel"; font-weight: 600; font-size: 11pt; letter-spacing: 0.26em; color: #d9b96b; }}
.back .imprint {{ position: absolute; left: 0.58in; right: 0.58in; bottom: 0.62in; font-family: "Inter"; font-size: 5.6pt; letter-spacing: 0.18em; text-transform: uppercase; color: #7e7664; }}
.back .barcode {{ position: absolute; right: 0.5in; bottom: 0.45in; width: 2in; height: 1.2in; background: #fff; color: #333; font-family: "Inter"; font-size: 6pt; text-align: center; padding-top: 0.52in; letter-spacing: 0.08em; }}
.spine .spine-inner {{ position: absolute; top: 50%; left: 50%; width: 7.6in; transform: translate(-50%, -50%) rotate(90deg); text-align: center; white-space: nowrap; }}
.spine .spine-title {{ font-family: "Cinzel"; font-weight: 600; font-size: 10.5pt; letter-spacing: 0.22em; color: #d9b96b; }}
.spine .spine-author {{ font-family: "Inter"; font-size: 6.6pt; letter-spacing: 0.2em; color: #c7bda8; margin-left: 0.35in; }}
</style></head>
<body>
<div class="panel back"><div class="inner">
  <div class="frame"></div><div class="frame-inner"></div>
  <div class="content">
    <div class="kicker">A Christ-Centred Theology and Practice</div>
    <div class="headline">The King is not merely stronger.<br>He is Lord.</div>
    <div class="blurb">
      <p>Jesus did not negotiate with demons or depend on their cooperation. He commanded, and they obeyed. <i>Divine Authority</i> recovers that vision for the church today: a deliverance ministry that begins with the identity of Christ, not the activity of the enemy.</p>
      <p>Drawing on the Gospels, the Epistles, and the original biblical languages, this book joins careful theology to sober pastoral practice.</p>
    </div>
    <div class="bullets">
      <div><b>·</b> A biblical theology of authority, power, and dominion</div>
      <div><b>·</b> Seven encounters with demons and unclean spirits</div>
      <div><b>·</b> A safe, ethical, person-centred ministry protocol</div>
      <div><b>·</b> A complete ten-lesson teaching curriculum</div>
      <div><b>·</b> Forms, checklists, aftercare plans, and study questions</div>
    </div>
  </div>
  <div class="author">{esc(cfg['author']).upper()}</div>
  <div class="imprint">{esc(cfg['publisher'])}</div>
  <div class="barcode">ISBN / BARCODE AREA</div>
</div></div>
<div class="panel spine"><div class="spine-inner">
  <span class="spine-title">DIVINE AUTHORITY</span><span class="spine-author">{esc(cfg['author']).upper()}</span>
</div></div>
<div class="panel front"><div class="inner">
  <div class="frame"></div><div class="frame-inner"></div>
  <div class="content">
    <div class="topline">Biblical Teaching · Christology · Spiritual Authority</div>
    <div class="cross"><span class="diamond"></span></div>
    <h1><span>DIVINE</span><span>AUTHORITY</span></h1>
    <div class="rule"></div>
    <div class="sub">Christ, Demons and Unclean Spirits</div>
    <div class="sub2">His Authority and Power Over Them</div>
    <div class="desc">A Christ-Centred Teaching Book and Practical Handbook for Deliverance Ministry</div>
  </div>
  <div class="author">{esc(cfg['author']).upper()}</div>
  <div class="imprint">{esc(cfg['publisher'])}</div>
</div></div>
</body></html>"""
    path = OUT / "Divine_Authority_Cover_Wrap.pdf"
    _weasyprint_html()(string=html_str, base_url=str(BOOK_DIR)).write_pdf(str(path))
    (OUT / "cover_wrap.html").write_text(html_str, encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# EPUB
# --------------------------------------------------------------------------

def build_epub(cfg: dict, epub_sections: list[dict],
               out_path: Path | None = None, use_cover: bool = True,
               identifier: str | None = None) -> Path:
    from ebooklib import epub

    book = epub.EpubBook()
    book.set_identifier(identifier or cfg.get("identifier") or f"divine-authority-{cfg['year']}")
    book.set_title(cfg["title"])
    book.set_language(cfg["language"])
    book.add_author(cfg["author"])
    book.add_metadata("DC", "publisher", cfg["publisher"])
    book.add_metadata("DC", "date", str(cfg["year"]))
    book.add_metadata("DC", "description", cfg["description"])
    for subject in cfg.get("subjects", [
        "Religion / Christian Theology / Christology",
        "Religion / Christian Ministry / Deliverance",
    ]):
        book.add_metadata("DC", "subject", subject)

    cover = OUT / "cover.jpg"
    if use_cover and cover.exists():
        book.set_cover("cover.jpg", cover.read_bytes())

    css = (BOOK_DIR / "styles" / "ebook.css").read_text(encoding="utf-8")
    style = epub.EpubItem(
        uid="style", file_name="style/ebook.css",
        media_type="text/css", content=css,
    )
    book.add_item(style)

    chapters = []
    for i, sec in enumerate(epub_sections):
        c = epub.EpubHtml(
            title=sec["title"],
            file_name=f"{sec['id']}.xhtml",
            lang=cfg["language"],
        )
        # Note: no <?xml ... encoding=?> declaration. lxml refuses to parse an
        # encoding declaration from a str, which makes ebooklib's own body
        # extraction silently return empty and fail the build. UTF-8 is the XML
        # default, so dropping the declaration is both valid and equivalent.
        c.content = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{cfg['language']}">
<head><title>{esc(sec['title'])}</title><link rel="stylesheet" href="style/ebook.css" type="text/css"/></head>
<body>{sec['html']}</body>
</html>"""
        c.add_item(style)
        book.add_item(c)
        chapters.append(c)

    book.toc = tuple(chapters)
    book.spine = ["nav"] + chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    path = out_path or (OUT / "Divine_Authority.epub")
    epub.write_epub(str(path), book, {})
    return path


# --------------------------------------------------------------------------
# DOCX
# --------------------------------------------------------------------------

def build_docx(cfg: dict, preface_body: str, sections: list[dict],
               out_path: Path | None = None, preface_title: str = "Preface") -> Path:
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    doc = Document()
    doc.core_properties.title = cfg["title"]
    doc.core_properties.author = cfg.get("copyright_holder", cfg["author"])
    doc.core_properties.subject = cfg.get("description", "")
    doc.core_properties.keywords = ", ".join(cfg.get("subjects", []))
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    doc.settings.element.append(update_fields)

    sec = doc.sections[0]
    sec.page_width = Inches(6)
    sec.page_height = Inches(9)
    sec.top_margin = Inches(0.72)
    sec.bottom_margin = Inches(0.78)
    sec.left_margin = Inches(0.8)
    sec.right_margin = Inches(0.62)

    normal = doc.styles["Normal"]
    normal.font.name = "EB Garamond"
    normal.font.size = Pt(11)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "EB Garamond")
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.15

    for name, size, color in [
        ("Heading 1", 24, "12263A"),
        ("Heading 2", 15, "23303D"),
        ("Heading 3", 10, "8A6A2F"),
    ]:
        st = doc.styles[name]
        st.font.name = "Cormorant Garamond"
        st.font.size = Pt(size)
        st.font.color.rgb = RGBColor.from_string(color)
        st.font.bold = True

    # Footer page number
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run()
    fld1 = OxmlElement("w:fldChar"); fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = " PAGE "
    fld2 = OxmlElement("w:fldChar"); fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1); run._r.append(instr); run._r.append(fld2)
    run.font.name = "Inter"; run.font.size = Pt(8)

    # Header
    hdr = sec.header.paragraphs[0]
    hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hr = hdr.add_run(cfg["title"].upper())
    hr.font.name = "Inter"; hr.font.size = Pt(7); hr.font.bold = True
    hr.font.color.rgb = RGBColor.from_string("9A8F78")

    # Title page
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(110)
    r = p.add_run(cfg["title"].upper()); r.font.name = "Cinzel"; r.font.size = Pt(40); r.font.bold = True
    r.font.color.rgb = RGBColor.from_string("12263A")

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    r = p.add_run(cfg["subtitle"]); r.font.name = "Cormorant Garamond"; r.font.size = Pt(18); r.font.bold = True
    r.font.color.rgb = RGBColor.from_string("2B3B4A")

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(cfg["subtitle2"]); r.font.name = "Cormorant Garamond"; r.font.italic = True; r.font.size = Pt(13)
    r.font.color.rgb = RGBColor.from_string("5A6672")

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(26)
    r = p.add_run(cfg["description"]); r.font.name = "Inter"; r.font.size = Pt(8)
    r.font.color.rgb = RGBColor.from_string("7D7463")

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(120)
    r = p.add_run(cfg["author"].upper()); r.font.name = "Cinzel"; r.font.size = Pt(14); r.font.bold = True
    r.font.color.rgb = RGBColor.from_string("12263A")

    doc.add_page_break()

    # Copyright
    cp = doc.add_paragraph()
    cp.paragraph_format.space_before = Pt(300)
    lines = [
        f"{cfg['title']}: {cfg['subtitle']}",
        f"Copyright © {cfg['year']} {cfg.get('copyright_holder', cfg['author'])}. All rights reserved.",
        f"{cfg['edition']}.",
        "Unless otherwise noted, Scripture quotations are from the Authorized (King James) Version, which is in the public domain.",
        "This book is a pastoral resource, not a substitute for medical, psychiatric, or emergency care.",
        f"Published by {cfg['publisher']}.",
    ]
    for line in lines:
        q = doc.add_paragraph()
        r = q.add_run(line); r.font.name = "Inter"; r.font.size = Pt(8)
        r.font.color.rgb = RGBColor.from_string("4B4740")

    doc.add_page_break()

    # TOC field
    p = doc.add_paragraph()
    r = p.add_run("Contents"); r.font.name = "Cinzel"; r.font.size = Pt(20); r.font.bold = True
    r.font.color.rgb = RGBColor.from_string("12263A")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph()
    run = p.add_run()
    fldChar = OxmlElement("w:fldChar"); fldChar.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText"); instrText.set(qn("xml:space"), "preserve")
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'
    fldChar2 = OxmlElement("w:fldChar"); fldChar2.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t"); t.text = "Right-click and choose Update Field to generate the table of contents."
    fldChar3 = OxmlElement("w:fldChar"); fldChar3.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar); run._r.append(instrText); run._r.append(fldChar2)
    run._r.append(t); run._r.append(fldChar3)

    doc.add_page_break()

    def add_inline(par, el):
        if el.text:
            par.add_run(el.text)
        for child in el:
            tag = child.tag
            if tag == "strong":
                r = par.add_run(child.text_content()); r.bold = True
            elif tag == "em":
                r = par.add_run(child.text_content()); r.italic = True
            elif tag == "code":
                r = par.add_run(child.text_content()); r.font.name = "Consolas"; r.font.size = Pt(9)
            elif tag == "a":
                r = par.add_run(child.text_content()); r.font.color.rgb = RGBColor.from_string("7A5B24")
            elif tag == "br":
                par.add_run().add_break()
            else:
                if child.text:
                    par.add_run(child.text)
                if child.tail:
                    par.add_run(child.tail)
            if child.tail:
                par.add_run(child.tail)

    def add_html_block(container, el):
        tag = el.tag
        if tag in ("h1", "h2", "h3"):
            level = {"h1": 1, "h2": 2, "h3": 3}[tag]
            p = container.add_paragraph(style=f"Heading {level}")
            add_inline(p, el)
        elif tag == "p":
            p = container.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_inline(p, el)
        elif tag == "blockquote":
            p = container.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.right_indent = Inches(0.2)
            for child in el:
                if child.tag == "p":
                    add_inline(p, child)
                    p.add_run("\n")
            for r in p.runs:
                r.italic = True
        elif tag in ("ul", "ol"):
            style = "List Bullet" if tag == "ul" else "List Number"
            for li in el.findall("li"):
                p = container.add_paragraph(style=style)
                p.paragraph_format.space_after = Pt(2)
                add_inline(p, li)
        elif tag == "table":
            rows = el.findall(".//tr")
            if not rows:
                return
            ncols = max(len(r.findall("th") + r.findall("td")) for r in rows)
            table = container.add_table(rows=0, cols=ncols)
            table.style = "Table Grid"
            for row in rows:
                cells = row.findall("th") + row.findall("td")
                tr = table.add_row()
                for i, cell in enumerate(cells[:ncols]):
                    para = tr.cells[i].paragraphs[0]
                    run = para.add_run(cell.text_content())
                    run.font.size = Pt(8.5)
                    if cell.tag == "th":
                        run.bold = True
        elif tag == "hr":
            p = container.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
        elif tag == "div":
            for child in el:
                add_html_block(container, child)

    # Front matter block (the Preface in the full book, "About" in a study)
    p = doc.add_paragraph(style="Heading 1")
    r = p.add_run(preface_title); r.font.name = "Cormorant Garamond"; r.font.size = Pt(24)
    pre_el = render_body(preface_body, add_lead=False, context="preface")
    for child in pre_el:
        add_html_block(doc, child)
    doc.add_page_break()

    for sec_data in sections:
        typ = sec_data["type"]
        if typ == "part":
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(180)
            r = p.add_run(f"PART {sec_data['part']}"); r.font.name = "Inter"; r.font.size = Pt(9); r.bold = True
            r.font.color.rgb = RGBColor.from_string("8A6A2F")
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(sec_data["title"]); r.font.name = "Cinzel"; r.font.size = Pt(24); r.bold = True
            r.font.color.rgb = RGBColor.from_string("12263A")
            doc.add_page_break()
            if sec_data["body"].strip():
                body_el = render_body(sec_data["body"], add_lead=False)
                for child in body_el:
                    add_html_block(doc, child)
                doc.add_page_break()
            continue

        doc.add_page_break()
        if typ in ("chapter", "appendix", "intro", "conclusion", "summary"):
            kicker = sec_data.get("kicker", "")
            if kicker:
                p = doc.add_paragraph()
                r = p.add_run(kicker.upper()); r.font.name = "Inter"; r.font.size = Pt(8); r.bold = True
                r.font.color.rgb = RGBColor.from_string("8A6A2F")
            p = doc.add_paragraph(style="Heading 1")
            r = p.add_run(sec_data["title"]); r.font.name = "Cormorant Garamond"; r.font.size = Pt(24)
            body_el = render_body(sec_data["body"], add_lead=False)
            for child in body_el:
                add_html_block(doc, child)
        else:
            p = doc.add_paragraph(style="Heading 1")
            p.add_run(sec_data["title"])
            body_el = render_body(sec_data["body"], add_lead=False)
            for child in body_el:
                add_html_block(doc, child)

    path = out_path or (OUT / "Divine_Authority.docx")
    doc.save(str(path))
    return path


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    cfg = load_config()
    preface_body, sections = parse_manuscript(cfg)

    print("Building interior PDF ...")
    pdf_path, page_count, entries = build_pdf(cfg, preface_body, sections)
    print(f"  {pdf_path} ({page_count} pages)")

    print("Building covers ...")
    front_pdf, cover_png = build_cover_front(cfg)
    wrap_pdf = build_cover_wrap(cfg, page_count)
    print(f"  {front_pdf}\n  {cover_png}\n  {wrap_pdf}")

    print("Building EPUB ...")
    epub_sections = json.loads((OUT / "epub_sections.json").read_text(encoding="utf-8"))
    epub_path = build_epub(cfg, epub_sections)
    print(f"  {epub_path}")

    print("Building DOCX ...")
    docx_path = build_docx(cfg, preface_body, sections)
    print(f"  {docx_path}")

    words = len(re.findall(r"\b\w+\b", (BOOK_DIR / cfg["source"]).read_text(encoding="utf-8")))
    report = {
        "title": cfg["title"],
        "author": cfg["author"],
        "pages": page_count,
        "words": words,
        "spine_in": round(page_count * cfg["spine_per_page_in"], 4),
        "trim": f"{cfg['trim']['width_in']} x {cfg['trim']['height_in']} in",
        "outputs": [p.name for p in OUT.iterdir() if p.is_file()],
    }
    (OUT / "build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
