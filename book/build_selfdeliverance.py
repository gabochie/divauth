#!/usr/bin/env python3
"""Package Self-Deliverance 101 MVP with the main book's build machinery.

The manuscript is Self_Deliverance_101_MVP.md; this driver supplies the
book-specific config, cover and output directory, and reuses build.py for
interior HTML, EPUB, DOCX and the shared CSS/font setup.
"""

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

PKG = build.ROOT / "Self_Deliverance_101"
OUT = PKG / "output"


def load_cfg() -> dict:
    return json.loads((PKG / "config.json").read_text(encoding="utf-8"))


def build_wrap(cfg: dict, pages: int) -> Path:
    """A print wrap around the supplied cover artwork."""
    prefix = cfg["out_prefix"]
    spine = max(0.25, pages * cfg["spine_per_page_in"])
    bleed = cfg["bleed_in"]
    width = 12 + spine + 2 * bleed
    height = 9 + 2 * bleed
    title = build.esc(cfg["title"])
    author = build.esc(cfg["author"]).upper()

    doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{title} — Cover</title><meta name="author" content="{build.esc(cfg['author'])}">
<style>
{build.cover_css(cfg)}
@page {{ size: {width:.4f}in {height:.4f}in; margin: 0; }}
body {{ margin: 0; width: {width:.4f}in; height: {height:.4f}in; background: #0a1420; }}
.panel {{ position: absolute; top: {bleed}in; height: 9in; }}
.back {{ left: {bleed}in; width: 6in; background: #0a1420; }}
.spine {{ left: {bleed + 6:.4f}in; width: {spine:.4f}in; background: #0a1420; }}
.front {{ left: {bleed + 6 + spine:.4f}in; top: 0; width: {6 + bleed:.4f}in; height: {9 + 2 * bleed:.4f}in; }}
.front img {{ width: {6 + bleed:.4f}in; height: {9 + 2 * bleed:.4f}in; display: block; }}
.back {{ box-sizing: border-box; padding: 0.7in 0.6in; color: #e9e1d0; }}
.kicker {{ font-family: Inter, sans-serif; font-size: 6pt; letter-spacing: .22em;
          text-transform: uppercase; color: #b9a878; }}
.headline {{ font-family: "Cormorant Garamond", serif; font-size: 21pt; font-weight: 600;
             line-height: 1.2; margin-top: 0.25in; color: #efe7d6; }}
.blurb {{ font-family: "EB Garamond", serif; font-size: 9pt; line-height: 1.5;
          margin-top: 0.22in; color: #d8d0bf; }}
.points {{ margin-top: 0.22in; font-family: Inter, sans-serif; font-size: 7pt;
           line-height: 1.7; color: #cfc6b3; }}
.byline {{ position: absolute; bottom: 0.8in; left: 0.6in; font-family: Cinzel, serif;
           font-size: 11pt; color: #d9b96b; letter-spacing: .18em; }}
.imprint {{ position: absolute; bottom: 0.55in; left: 0.6in; font-family: Inter, sans-serif;
            font-size: 5.5pt; letter-spacing: .16em; text-transform: uppercase; color: #7e7664; }}
.barcode {{ position: absolute; right: 0.5in; bottom: 0.45in; width: 2in; height: 1.2in;
            background: #fff; color: #333; font-family: Inter, sans-serif; font-size: 6pt;
            text-align: center; padding-top: 0.52in; letter-spacing: .08em; }}
.spine-in {{ position: absolute; top: 50%; left: 50%; width: 7.6in;
             transform: translate(-50%, -50%) rotate(90deg); text-align: center;
             white-space: nowrap; }}
.spine-title {{ font-family: Cinzel, serif; font-size: 10pt; letter-spacing: .2em; color: #d9b96b; }}
.spine-author {{ font-family: Inter, sans-serif; font-size: 6pt; letter-spacing: .2em;
                 color: #c7bda8; margin-left: .3in; }}
</style></head><body>
<div class="panel back">
  <div class="kicker">A Field Manual for Personal Spiritual Liberation</div>
  <div class="headline">You do not have to remain in bondage to what Christ has already defeated.</div>
  <div class="blurb">
    <p>Deliverance is the beginning of a transformed life, not the final destination.
    This field manual walks through the authority of Christ, the nature of bondage,
    and a biblical, safe, practical response.</p>
  </div>
  <div class="points">
    &bull; F.R.E.E.D.O.M. — seven movements toward freedom<br>
    &bull; Twenty-seven chapters across four parts<br>
    &bull; Exercises, tools and a 30-day renewal starter<br>
    &bull; Safeguards: no self-diagnosis, no abandonment of care
  </div>
  <div class="byline">{author}</div>
  <div class="imprint">{title} &middot; {build.esc(cfg['edition'])}</div>
  <div class="barcode">ISBN / BARCODE AREA</div>
</div>
<div class="panel spine"><div class="spine-in">
  <span class="spine-title">{title.upper()}</span>
  <span class="spine-author">{author}</span>
</div></div>
<div class="panel front"><img src="../Self_Deliverance_101/cover_source.png" alt="Cover"></div>
</body></html>"""

    path = OUT / f"{prefix}_Cover_Wrap.pdf"
    build._weasyprint_html()(string=doc, base_url=str(build.BOOK_DIR)).write_pdf(str(path))
    (OUT / "cover_wrap.html").write_text(doc, encoding="utf-8")
    return path


def main() -> int:
    build.OUT = OUT
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_cfg()
    prefix = cfg["out_prefix"]

    preface, sections = build.parse_manuscript(cfg)
    chapters = sum(1 for s in sections if s["type"] == "chapter")
    print(f"Manuscript: {len(sections)} sections, {chapters} chapters")

    # Interior PDF + the HTML/EPUB intermediates
    preface_html = LH.tostring(
        build.render_body(preface, add_lead=False, context="preface"),
        encoding="unicode", method="html",
    )
    # Measure real anchor positions so the printed contents page has page
    # numbers (the same iterative pass build.py:build_pdf performs).
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
    page_numbers: dict[str, str] = {}
    for entry in entries:
        idx = anchors.get(entry["id"])
        if idx is None:
            continue
        if entry["kind"] == "front":
            page_numbers[entry["id"]] = build.roman(idx + 1)
        else:
            page_numbers[entry["id"]] = str(idx - intro_i + 1)

    main_html, entries, epub_sections = build.build_main(cfg, sections, spacer)
    entries = [build.toc_entry(0, "Preface", "preface", "front")] + entries
    html_str = build.build_html(cfg, preface_html, main_html, entries, page_numbers)
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

    # Cover artwork -> print front + EPUB cover JPEG
    src = build.BOOK_DIR / cfg["cover_source"]
    img = Image.open(src).convert("RGB").resize((1800, 2700), Image.LANCZOS)
    img.save(OUT / "cover.jpg", quality=90)
    front = OUT / f"{prefix}_Cover_Front.pdf"
    img.save(str(front), "PDF", resolution=300.0,
             title=cfg["title"], author=cfg["author"])
    print(f"  {front.name}")
    wrap = build_wrap(cfg, pages)
    print(f"  {wrap.name}")

    epub = build.build_epub(cfg, epub_sections,
                            out_path=OUT / f"{prefix}.epub", use_cover=True,
                            identifier=cfg.get("identifier"))
    print(f"  {epub.name}")
    docx = build.build_docx(cfg, preface, sections,
                            out_path=OUT / f"{prefix}.docx")
    print(f"  {docx.name}")

    words = len(re.findall(r"\b\w+\b", (build.BOOK_DIR / cfg["source"]).read_text(encoding="utf-8")))
    report = {
        "title": cfg["title"],
        "author": cfg["author"],
        "edition": cfg["edition"],
        "pages": pages,
        "words": words,
        "chapters": chapters,
        "spine_in": round(pages * cfg["spine_per_page_in"], 4),
        "trim": "6 x 9 in",
        "cover": cfg["cover_source"],
        "outputs": sorted(p.name for p in OUT.iterdir() if p.is_file()),
    }
    (OUT / "build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
