# DivAuth — book projects

Three books are built from this repository. Each has one canonical manuscript and a build that generates print and digital outputs.

| # | Book | Canonical manuscript | Outputs | Status |
|---|---|---|---|---|
| 1 | **Divine Authority** — *Christ, Demons and Unclean Spirits* | `Divine_Authority_Teaching_Book.md` | `book/output/` | Complete — 170 pp, 18,850 words |
| 2 | **Seven Sons of Sceva** — *A Case Study in Counterfeit Authority* | generated from §7.5 of book 1 | `book/output/study/` | Complete — companion study, 4 formats |
| 3 | **Self-Deliverance 101** — *The Freedom Field Manual* (MVP Release 1) | `Self_Deliverance_101_MVP.md` | `Self_Deliverance_101/output/` | Complete draft — 162 pp, 22,744 words |

## Building

From `book/`:

```powershell
# book 1 — main volume (needs GTK3 runtime + poppler for PDF/covers)
python build.py

# book 2 — standalone Sceva study (generated from book 1's section 7.5)
python build_study.py

# book 3 — Self-Deliverance 101 MVP
python build_selfdeliverance.py
```

Windows dependencies for the PDF stages:
- GTK3 runtime (`C:\Program Files\GTK3-Runtime Win64\bin`) for WeasyPrint/Pango
- Poppler (`pdftoppm`) for the book 1 cover JPEG

Python packages: `markdown`, `lxml`, `weasyprint`, `ebooklib`, `python-docx`, `Pillow`.

## Source documents and verification

The original research files are preserved untouched:

| Source | Folded into |
|---|---|
| `DivAuth`, `diva` (+ `.backup`) | `Divine_Authority_Teaching_Book.md` |
| `7SonsSceva` | §7.5 and §9.1 of book 1; book 2 |
| `casestudy` | §4.10 of book 1 |
| `SelF Deliverance 101.txt` (Desktop) | `Self_Deliverance_101_MVP.md` |

Verification reports:

- `Research_Verification_Report.md` — books 1 and 2 (original lexical work plus the Sceva/case-study sources, §11)
- `Self_Deliverance_101_Verification_Report.md` — book 3 (116/116 KJV quotations verified)

## Editorial note

Every book is Christ-centred and includes pastoral-safety material: no self-diagnosis of demon possession from symptoms, no abandonment of medical or mental-health care, no physical restraint or deprivation, informed consent, and referral criteria. These are part of the teaching, not an appendix afterthought.
