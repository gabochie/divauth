#!/usr/bin/env python3
"""Generate standalone companion studies from the Divine Authority manuscript.

The teaching book is the single source of truth. This script extracts a
section of it and wraps it as a self-contained study, so a study can be
handed out on its own without the two documents ever drifting apart.

Outputs, per study, land in book/output/study/:

    <slug>.md      the extracted, portable source text
    <slug>.epub    for screens and e-readers
    <slug>.docx    for printing and editing
    <slug>.pdf     only where WeasyPrint's Pango/GObject runtime is present

Usage:
    python build_study.py              # build every study
    python build_study.py sceva        # build studies whose slug matches
"""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

from lxml import html as LH

import build

STUDY_DIR = build.OUT / "study"


STUDIES = [
    {
        "slug": "Seven_Sons_of_Sceva",
        "match": "sceva",
        "ref": "7.5",
        "title": "The Sons of Sceva",
        "subtitle": "A Case Study in Counterfeit Authority",
        "kicker": "Companion Study",
        # The canonical text lives in the teaching book; this is only a pointer.
        "chapter": "Chapter 7 — The Name of Jesus and Delegated Authority",
        "start": "## 7.5 ",
        "stop": "## 7.6 ",
        "heading": "The Sons of Sceva: A Warning Against Counterfeit Authority",
        "summary": (
            "Seven travelling exorcists in Ephesus took the name of Jesus and used it "
            "the way they used every other name in their repertoire — as a formula. "
            "The result is the most memorable failure in the Book of Acts, and the "
            "clearest warning the New Testament gives about counterfeit spiritual "
            "authority."
        ),
    },
]


# --------------------------------------------------------------------------
# Extraction — always from the manuscript, never from a copy
# --------------------------------------------------------------------------

def manuscript_sections() -> tuple[dict, list[tuple[str, str]]]:
    cfg = build.load_config()
    raw = (build.BOOK_DIR / cfg["source"]).read_text(encoding="utf-8")
    matches = list(build.TOP_RE.finditer(raw))
    if len(matches) < 2:
        raise SystemExit("No top-level headings found in manuscript.")
    sections = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        sections.append((m.group(1).strip(), raw[m.end():end]))
    return cfg, sections


def extract(sections: list[tuple[str, str]], study: dict) -> str:
    body = next((b for h, b in sections if h == study["chapter"]), None)
    if body is None:
        raise SystemExit(f"Study chapter not found: {study['chapter']}")

    start = body.find(study["start"])
    if start < 0:
        raise SystemExit(f"Study start marker not found: {study['start']}")
    stop = body.find(study["stop"], start)
    if stop < 0:
        stop = len(body)

    lines = body[start:stop].strip().split("\n")

    # Drop the section number: "## 7.5 The sons of Sceva ..." would make no
    # sense once it stands on its own.
    if not lines[0].startswith(study["start"]):
        raise SystemExit(f"Study does not open on its marker: {lines[0]!r}")
    lines[0] = "## " + study["heading"]

    return "\n".join(lines)


def study_title_of(cfg: dict, study: dict) -> str:
    return f"{study['title']}: {study['subtitle']}"


def about_text(cfg: dict, study: dict) -> str:
    """Front block shared by the EPUB and DOCX; their own headings title it."""
    return (
        f"**A companion study from** *{cfg['title']}: {cfg['subtitle']}*, "
        f"by {cfg['author']}.\n\n"
        "This study is **generated directly from the teaching book**, at §"
        f"{study['ref']} of {study['chapter']}. It is not a separate composition: "
        "where the two ever differ, the book is authoritative.\n\n"
        "Scripture quotations are from the Authorized (King James) Version unless "
        "otherwise noted. Claims offered as scholarly proposals rather than lexical "
        "or historical fact are labelled as such.\n\n"
        "This material is a theological and pastoral resource. It is **not** a "
        "substitute for medical care, psychiatric care, counselling, or emergency "
        "services. Read the safeguarding chapter of the book before any practical "
        "use.\n"
    )


def study_markdown(cfg: dict, study: dict, about_md: str, excerpt: str) -> str:
    return (
        f"# {study['title']}\n\n"
        f"## {study['subtitle']}\n\n"
        f"**A companion study from** *{cfg['title']}: {cfg['subtitle']}*\n\n"
        f"**Author:** {cfg['author']}\n\n"
        "---\n\n"
        f"{study['summary']}\n\n"
        "---\n\n"
        f"{excerpt}\n\n"
        "---\n\n"
        f"{about_md}\n\n"
        f"**Source:** §{study['ref']} of `{cfg['source']}` "
        f"({study['chapter']}).\n"
    )


def to_html(md_text: str) -> str:
    el = build.render_body(md_text, add_lead=False, context="study")
    return LH.tostring(el, encoding="unicode", method="html")


# --------------------------------------------------------------------------
# Outputs
# --------------------------------------------------------------------------

def write_markdown(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_epub(cfg: dict, study: dict, about_md: str, excerpt: str, path: Path) -> Path:
    study_cfg = dict(cfg, title=study["title"], subtitle=study["subtitle"],
                     description=study["summary"])
    sections = [
        {"title": "About this study", "id": "about", "html": to_html(about_md)},
        {"title": study["heading"], "id": "study", "html": to_html(excerpt)},
    ]
    return build.build_epub(
        study_cfg, sections, out_path=path, use_cover=False,
        identifier=f"divine-authority-study-{study['match']}-{cfg['year']}",
    )


def write_docx(cfg: dict, study: dict, about_md: str, excerpt: str, path: Path) -> Path:
    study_cfg = dict(cfg, title=study["title"], subtitle=study["subtitle"],
                     subtitle2=study["kicker"], description=study["summary"])
    sections = [{
        "type": "chapter",
        "kicker": study["kicker"],
        "title": study["heading"],
        "body": excerpt,
    }]
    return build.build_docx(study_cfg, about_md, sections,
                            out_path=path, preface_title="About this study")


def write_pdf(study: dict, about_md: str, excerpt: str, path: Path) -> Path | None:
    # WeasyPrint prints its own troubleshooting banner while failing to import;
    # swallow it so a skipped PDF reads as a note, not as a build error.
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            from weasyprint import HTML  # noqa: PLC0415
    except Exception as exc:  # Pango/GObject native runtime absent
        print(f"  PDF skipped — WeasyPrint unavailable ({type(exc).__name__})")
        return None

    doc_html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{build.esc(study_title_html(study))}</title>"
        '<link rel="stylesheet" href="styles/print.css"></head>'
        f"<body><main>{to_html(about_md)}{to_html(excerpt)}</main></body></html>"
    )
    HTML(string=doc_html, base_url=str(build.BOOK_DIR)).write_pdf(str(path))
    return path


def study_title_html(study: dict) -> str:
    return f"{study['title']}: {study['subtitle']}"


# --------------------------------------------------------------------------

def build_one(cfg: dict, sections: list[tuple[str, str]], study: dict) -> list[Path]:
    excerpt = extract(sections, study)
    about_md = about_text(cfg, study)

    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Building study: {study_title_of(cfg, study)}")

    outputs = [
        write_markdown(STUDY_DIR / f"{study['slug']}.md",
                       study_markdown(cfg, study, about_md, excerpt)),
        write_epub(cfg, study, about_md, excerpt, STUDY_DIR / f"{study['slug']}.epub"),
        write_docx(cfg, study, about_md, excerpt, STUDY_DIR / f"{study['slug']}.docx"),
        write_pdf(study, about_md, excerpt, STUDY_DIR / f"{study['slug']}.pdf"),
    ]
    for path in outputs:
        if path is not None:
            print(f"  {path}")
    return [p for p in outputs if p is not None]


def main(argv: list[str]) -> int:
    cfg, sections = manuscript_sections()
    wanted = [a.lower() for a in argv[1:]]
    picked = [s for s in STUDIES
              if not wanted
              or any(w in s["match"] or w in s["slug"].lower() for w in wanted)]
    if not picked:
        raise SystemExit("No study matched: " + ", ".join(argv[1:]))

    written: list[Path] = []
    for study in picked:
        written += build_one(cfg, sections, study)

    print(f"\n{len(written)} file(s) written to {STUDY_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
