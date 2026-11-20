#!/usr/bin/env python3
"""Package Soft Life God's Way using the shared book build machinery."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from lxml import html as LH
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402

PKG = build.ROOT / "Soft Life God's Way"
OUT = PKG / "output"


def load_cfg() -> dict:
    return json.loads((PKG / "config.json").read_text(encoding="utf-8"))


COVER_CSS = """
@font-face { font-family: "Cinzel"; src: url("assets/fonts/cinzel-600-normal.ttf"); }
@font-face { font-family: "Cormorant Garamond"; src: url("assets/fonts/cormorant-garamond-400-normal.ttf"); }
@font-face { font-family: "Inter"; src: url("assets/fonts/inter-400-normal.ttf"); }
"""


def cover_html(cfg: dict) -> str:
    title = build.esc(cfg["title"].upper().replace(" ", "<br>"))
    subtitle = build.esc(cfg["subtitle"])
    author = build.esc(cfg["author"]).upper()
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{COVER_CSS}
@page {{ size: 6in 9in; margin: 0; }}
body {{ margin:0; width:6in; height:9in; background:#f3efe6; color:#2d3a35; }}
.cover {{ position:relative; width:6in; height:9in; box-sizing:border-box;
          border:0.7pt solid #9b8a63; padding:0.6in; }}
.inner {{ position:absolute; inset:0.18in; border:0.35pt solid #c3b590; }}
.content {{ position:absolute; top:1.35in; left:0.72in; right:0.72in; }}
.kicker {{ font-family:Inter,sans-serif; font-size:6pt; letter-spacing:.28em;
           text-transform:uppercase; color:#6d7a6a; text-align:center; }}
h1 {{ font-family:Cinzel,serif; font-size:36pt; line-height:1.15; text-align:center;
      color:#2d3a35; margin-top:0.55in; }}
.rule {{ width:1.4in; border-top:0.6pt solid #9b8a63; margin:0.35in auto; }}
.sub {{ font-family:"Cormorant Garamond",serif; font-size:13pt; line-height:1.4;
        text-align:center; color:#45534c; }}
.sub2 {{ font-family:Inter,sans-serif; font-size:7pt; letter-spacing:.18em;
         text-transform:uppercase; text-align:center; color:#6d7a6a; margin-top:0.3in; }}
.frame {{ font-family:"Cormorant Garamond",serif; font-style:italic; font-size:9pt;
          text-align:center; color:#6d7a6a; margin-top:0.45in; }}
.author {{ position:absolute; bottom:0.85in; left:0.6in; right:0.6in;
           font-family:Cinzel,serif; font-size:11pt; letter-spacing:.2em;
           text-align:center; color:#2d3a35; }}
.imprint {{ position:absolute; bottom:0.45in; left:0.6in; right:0.6in;
            font-family:Inter,sans-serif; font-size:5.5pt; letter-spacing:.18em;
            text-transform:uppercase; text-align:center; color:#8a8878; }}
</style></head><body>
<div class="cover"><div class="inner"><div class="content">
<div class="kicker">A Field Manual for Christian Women</div>
<h1>{title}</h1>
<div class="rule"></div>
<div class="sub">{subtitle}</div>
<div class="sub2">A Field Manual for Rest, Boundaries and Divine Alignment</div>
<div class="frame">Christ is the Deliverer; this manual teaches the believer's response.</div>
</div>
<div class="author">{author}</div>
<div class="imprint">{build.esc(cfg['publisher'])}</div>
</div></div></body></html>"""


def wrap_html(cfg: dict, pages: int) -> str:
    spine = max(0.25, pages * cfg["spine_per_page_in"])
    bleed = cfg["bleed_in"]
    width = 12 + spine + 2 * bleed
    height = 9 + 2 * bleed
    title = build.esc(cfg["title"])
    author = build.esc(cfg["author"]).upper()
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{title} — Cover</title><meta name="author" content="{build.esc(cfg['author'])}">
<style>
{COVER_CSS}
@page {{ size: {width:.4f}in {height:.4f}in; margin:0; }}
body {{ margin:0; width:{width:.4f}in; height:{height:.4f}in; background:#f3efe6; color:#2d3a35; }}
.panel {{ position:absolute; top:{bleed}in; height:9in; }}
.front {{ left:{bleed + 6 + spine:.4f}in; top:0; width:{6 + bleed:.4f}in;
          height:{9 + 2 * bleed:.4f}in; }}
.front img {{ width:{6 + bleed:.4f}in; height:{9 + 2 * bleed:.4f}in; display:block; }}
.back {{ left:{bleed}in; width:6in; box-sizing:border-box; padding:0.65in 0.55in;
         border:0.5pt solid #c3b590; }}
.kicker {{ font-family:Inter,sans-serif; font-size:6pt; letter-spacing:.22em;
           text-transform:uppercase; color:#6d7a6a; }}
.headline {{ font-family:"Cormorant Garamond",serif; font-size:20pt; font-weight:600;
             line-height:1.2; margin-top:0.22in; }}
.blurb {{ font-family:"Cormorant Garamond",serif; font-size:9.5pt; line-height:1.5;
          margin-top:0.2in; }}
.points {{ margin-top:0.18in; font-family:Inter,sans-serif; font-size:7pt; line-height:1.7; }}
.byline {{ position:absolute; bottom:0.8in; left:0.55in; right:0.55in;
           font-family:Cinzel,serif; font-size:8.5pt; letter-spacing:.08em; }}
.imprint {{ position:absolute; bottom:0.5in; left:0.55in; font-family:Inter,sans-serif;
            font-size:5.5pt; letter-spacing:.16em; text-transform:uppercase; color:#8a8878; }}
.spine {{ left:{bleed + 6:.4f}in; width:{spine:.4f}in; background:#f3efe6;
          border-left:0.4pt solid #c3b590; border-right:0.4pt solid #c3b590; }}
.spin {{ position:absolute; top:50%; left:50%; width:7.6in;
         transform:translate(-50%,-50%) rotate(90deg); text-align:center; white-space:nowrap; }}
.spin b {{ font-family:Cinzel,serif; font-size:10pt; letter-spacing:.18em; color:#2d3a35; }}
.spin span {{ font-family:Inter,sans-serif; font-size:6.5pt; letter-spacing:.18em; color:#6d7a6a;
              margin-left:0.3in; }}
.barcode {{ position:absolute; right:0.45in; bottom:0.4in; width:2in; height:1.2in;
            background:#fff; color:#333; font-family:Inter,sans-serif; font-size:6pt;
            text-align:center; padding-top:0.52in; letter-spacing:.08em; }}
</style></head><body>
<div class="panel back">
  <div class="kicker">Rest · Boundaries · Divine Alignment</div>
  <div class="headline">You were not made for survival mode.</div>
  <div class="blurb">
    <p>A soft life God's way is not luxury or escape. It is a life of surrender, peace
    and gentleness with boundaries — lived in the middle of an ordinary, complicated week.</p>
  </div>
  <div class="points">
    &bull; Surrender over striving &nbsp;&bull; Peace over luxury<br>
    &bull; Gentleness with boundaries &nbsp;&bull; 27 chapters and a 30-day rhythm
  </div>
  <div class="byline">{author}</div>
  <div class="imprint">{title}</div>
  <div class="barcode">ISBN / BARCODE AREA</div>
</div>
<div class="panel spine"><div class="spin"><b>{title.upper()}</b><span>{author}</span></div></div>
<div class="panel front"><img src="../Soft Life God's Way/output/cover.jpg" alt="Cover"></div>
</body></html>"""


def main() -> int:
    build.OUT = OUT
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_cfg()
    prefix = cfg["out_prefix"]
    preface, sections = build.parse_manuscript(cfg)
    chapters = sum(1 for s in sections if s["type"] == "chapter")
    print(f"Manuscript: {len(sections)} sections, {chapters} chapters")

    preface_html = LH.tostring(
        build.render_body(preface, add_lead=False, context="preface"),
        encoding="unicode", method="html",
    )

    spacer = False
    anchors: dict[str, int] = {}
    for _ in range(4):
        main_html, entries, epub_sections = build.build_main(cfg, sections, spacer)
        entries = [build.toc_entry(0, "Preface", "preface", "front")] + entries
        html_str = build.build_html(cfg, preface_html, main_html, entries, None)
        doc = build._weasyprint_html()(string=html_str, base_url=str(build.BOOK_DIR)).render()
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
    pages_map: dict[str, str] = {}
    for entry in entries:
        idx = anchors.get(entry["id"])
        if idx is None:
            continue
        if entry["kind"] == "front":
            pages_map[entry["id"]] = build.roman(idx + 1)
        else:
            pages_map[entry["id"]] = str(idx - intro_i + 1)

    main_html, entries, epub_sections = build.build_main(cfg, sections, spacer)
    entries = [build.toc_entry(0, "Preface", "preface", "front")] + entries
    html_str = build.build_html(cfg, preface_html, main_html, entries, pages_map)
    (OUT / "interior.html").write_text(html_str, encoding="utf-8")
    doc = build._weasyprint_html()(string=html_str, base_url=str(build.BOOK_DIR)).render()
    interior = OUT / f"{prefix}_Interior_6x9.pdf"
    doc.write_pdf(str(interior))
    pages = len(doc.pages)
    print(f"  {interior.name} — {pages} pages")

    (OUT / "epub_sections.json").write_text(
        json.dumps(epub_sections, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "preface.html").write_text(preface_html, encoding="utf-8")

    # Supplied cover artwork -> print front PDF + EPUB JPEG
    src = build.BOOK_DIR / cfg["cover_source"]
    img = Image.open(src).convert("RGB").resize((1800, 2700), Image.LANCZOS)
    img.save(OUT / "cover.jpg", quality=82, optimize=True)
    front = OUT / f"{prefix}_Cover_Front.pdf"
    img.save(str(front), "PDF", resolution=300.0,
             title=cfg["title"], author=cfg["author"])
    print(f"  {front.name}")

    wrap = wrap_html(cfg, pages)
    (OUT / "cover_wrap.html").write_text(wrap, encoding="utf-8")
    wrap_pdf = OUT / f"{prefix}_Cover_Wrap.pdf"
    build._weasyprint_html()(string=wrap, base_url=str(build.BOOK_DIR)).write_pdf(str(wrap_pdf))
    print(f"  {wrap_pdf.name}")

    # EPUB readers should open on a title page, not on the Introduction.
    title_page = (
        f'<h1 class="chapter-title">{build.esc(cfg["title"])}</h1>'
        f'<p>{build.esc(cfg["subtitle"])}</p>'
        f'<p><em>{build.esc(cfg["subtitle2"])}</em></p>'
        f'<p>{build.esc(cfg["author"])}</p>'
    )
    copyright_page = (
        '<h1 class="chapter-title">Copyright</h1>'
        f'<p>Copyright © {cfg["year"]} {build.esc(cfg["copyright_holder"])}. '
        'All rights reserved.</p>'
        f'<p>{build.esc(cfg["edition"])}.</p>'
        '<p>Unless otherwise noted, Scripture quotations are from the Authorized '
        '(King James) Version, which is in the public domain.</p>'
        '<p>This book is a pastoral and practical resource. It is not a substitute '
        'for medical, psychiatric, or emergency care.</p>'
        f'<p>Published by {build.esc(cfg["publisher"])}.</p>'
    )
    epub_sections = [
        {"id": "titlepage", "title": "Title page", "html": title_page},
        {"id": "copyright", "title": "Copyright", "html": copyright_page},
        {"id": "preface", "title": "Preface", "html": preface_html},
    ] + epub_sections

    epub = build.build_epub(cfg, epub_sections, out_path=OUT / f"{prefix}.epub",
                            use_cover=True, identifier=cfg.get("identifier"))
    print(f"  {epub.name}")
    docx = build.build_docx(cfg, preface, sections, out_path=OUT / f"{prefix}.docx")
    print(f"  {docx.name}")

    words = len(re.findall(r"\b\w+\b", (build.BOOK_DIR / cfg["source"]).read_text(encoding="utf-8")))
    report = {
        "title": cfg["title"],
        "subtitle": cfg["subtitle"],
        "author": cfg["author"],
        "edition": cfg["edition"],
        "pages": pages,
        "words": words,
        "chapters": chapters,
        "spine_in": round(pages * cfg["spine_per_page_in"], 4),
        "trim": "6 x 9 in",
        "outputs": sorted(p.name for p in OUT.iterdir() if p.is_file()),
    }
    (OUT / "build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
