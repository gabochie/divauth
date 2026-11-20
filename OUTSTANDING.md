# Outstanding items

A single place for everything deliberately left undone. Last updated: **20 November 2026**.

Legend: **BLOCKER** = must be resolved before public distribution · **DECISION** = needs an editorial choice · **NICE** = can wait.

---

## All books

| # | Severity | Item | Detail |
|---|---|---|---|
| A1 | **BLOCKER** | Assign ISBNs | All four books have `"isbn": ""`. Each print edition needs an ISBN/EAN before retail distribution. The back covers carry marked white barcode zones. |
| A2 | **BLOCKER** | Native-resolution cover files | Supplied artwork is 1024 × 1536 px (~171 dpi at 6 × 9 in) and is upscaled to 1800 × 2700. Fine for ebook/proof; commission native 300 dpi files before a print run. |
| A3 | NICE | Refresh book 1's TOC text files | `book/output/toc.txt` and `toc2.txt` are manual extracts from an earlier PDF and do not match the current 170-page build. No generator exists in the repo. |

## Book 1 — Divine Authority

| # | Severity | Item | Detail |
|---|---|---|---|
| 1a | NICE | TOC text files | See A3 above. |
| 1b | NICE | Flat EPUB navigation | Chapters are not nested under Parts; book 1's EPUB also lacks title/copyright/preface front matter. House-standard defect, not introduced by the later books. |

## Book 2 — Seven Sons of Sceva

No outstanding items recorded. All four formats build and verify cleanly.

## Book 3 — Self-Deliverance 101

| # | Severity | Item | Detail |
|---|---|---|---|
| 3a | **BLOCKER** | ISBN | See A1. |
| 3b | **BLOCKER** | Native cover art | See A2. Supplied PNG is 1024 × 1536. |
| 3c | **DECISION** | Cover style | Cartoon artwork with smiling star mascot vs the dark navy/gold house style of book 1. Packaged with the supplied art; keep or replace is your call. |
| 3d | NICE | Word count | 23,616 words against the brief's 24,000 lower bound — about 400 words short. Structurally complete. |
| 3e | NICE | Parts Five to Seven | Not written; deferred by the product brief to a later release. |
| 3f | NICE | Full 30-Day Programme | Only the starter is included. |
| 3g | NICE | Companion workbook / launch assets | Sales page copy, KDP/Selar listing, lead magnet ("7-Day Freedom Starter") and cohort are specified in the ecosystem docs on the Desktop but not built here. |

## Book 4 — Soft Life God's Way

| # | Severity | Item | Detail |
|---|---|---|---|
| 4a | **BLOCKER** | ISBN | See A1. |
| 4b | **BLOCKER** | Native cover art | See A2. |
| 4c | **DECISION** | Cover vs audience | The supplied cover shows a whole family with a cartoon star mascot, while the book addresses Christian women directly. Decision made on 20 Nov 2026: **keep the supplied cover**. Revisit if positioning changes. |
| 4d | **DECISION** | Design language | Cartoon front vs cream/gold typographic back and spine. Kept deliberately; can be harmonised later. |
| 4e | NICE | Page economy | 139 pages for 15,826 words (~114 words/page). `break-before: right` on every chapter plus short part-intro pages leaves sparse pages. Left as house style. |
| 4f | **DECISION** | Product identity | "Teaching Notes" after every chapter reads as group-study apparatus in a book positioned as a personal field manual. Decide: trade book or study edition. |
| 4g | NICE | Word count | ~15,800 words, well below the 22,000–24,000 words originally proposed. Chapters were kept tight rather than padded. Natural expansion points: composite illustrations and practice chapters. |
| 4h | NICE | Fourth subtitle variant | "A Joyful Family Journey" exists only in the cover filename and `Soft Life God's Way/Subtitle_Options.md`. Confirm whether to use it anywhere. |
| 4i | NICE | EPUB niceties | `cover.xhtml` remains outside the spine (cover is surfaced via metadata); no chapter nesting in the EPUB nav. |

---

## Decisions already made (do not re-open by accident)

- Primary subtitle for book 4: **option 1**; all three options plus the filename variant are preserved in `Soft Life God's Way/Subtitle_Options.md`.
- Book 4 audience: **Christian women**.
- Book 4 cover: **keep the supplied illustration**.
- Running headers are config-driven; books 3 and 4 must not inherit "DIVINE AUTHORITY".
- Safeguarding language in all books is fixed doctrine, not optional copy.

## How to use this file

When an item is resolved, delete its row and add a one-line note to `README.md` or the relevant verification report. When a new audit produces findings, add them here rather than leaving them in chat.
