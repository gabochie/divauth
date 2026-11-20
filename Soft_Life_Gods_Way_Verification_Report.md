# Verification Report — Soft Life God's Way (Volume One)

**Manuscript:** `Soft_Life_Gods_Way_MVP.md` (27 chapters, four parts, four appendices plus two further appendices)
**Source brief:** `Soft Life God's Way/Soft Life God's Way.txt` (895 words) — a positioning brief, not a manuscript
**Subtitle options:** all three preserved verbatim in `Soft Life God's Way/Subtitle_Options.md`; option 1 is primary
**Source map:** `Soft Life God's Way/Source_Preservation.md`
**Outputs:** `Soft Life God's Way/output/`
**Verification date:** 20 November 2026

## 1. Scripture quotations

Every attributed KJV blockquote was checked mechanically against the KJV text retrieved from BibleHub.

| Measure | Result |
|---|---|
| Attributed quotations found | 106 |
| Exact matches | **106 / 106** |
| Misquotations remaining | **0** |

Eleven errors were found and corrected during verification: 1 Peter 5:7 (*Casting*, not *Cast*), Ecclesiastes 4:6 (*an handful*), Mark 3:4 (*saith*), John 11:43 (*thus had spoken*), Matthew 12:12 (correct clause), 1 John 3:1 (*Behold*), Exodus 31:15 (*may work be done*), Hebrews 10:25 (*ourselves*), Matthew 8:17 (*Himself took*), Matthew 12:44–45 (split into two exact verses), Matthew 12:45 (*with himself*).

## 2. Source preservation

The source brief's substantive ideas are all carried into the book; the mapping is in `Source_Preservation.md`:

- the definition (divine alignment, grace, health, joy, stress reduction, not the removal of all difficulty),
- the three marks: surrender over striving, inner peace over luxury, strength with gentleness,
- the three practical habits: rest rhythms, guarding mind and body, contentment,
- the survival-mode and "chaotic rhythms" themes,
- Matthew 11:28 as the controlling text.

All **three subtitle options** are preserved verbatim, including the original recommendation to use option 1. Options 2 and 3 are retained as marketing variants. Option 3's "stress-free" promise was not adopted as the book subtitle because the source's own definition and John 16:33 contradict it; the reasoning is recorded in the options file.

## 3. What was deliberately excluded

- Unverified named attributions from search snippets (Jasmine Rutledge, She Ministries, several Facebook/Instagram/YouTube sources, a named pastor, Calm). The book cites Scripture instead.
- Retrieval artefacts: view counts, durations, upload ages, tracking URLs.
- Chat artefacts: "Would you like to focus on…?", "Use the highlighted definition to creat[…]", "I would go with the first option…".

## 4. Theological guardrails

| Risk | How the manuscript handles it |
|---|---|
| "Soft life" as prosperity teaching | Chapters 1, 6, 19 and the Conclusion state that biblical peace is not the absence of trials (John 16:33; Revelation 21:4) |
| Rest as laziness | Chapter 8 holds diligence and rest together (Ecclesiastes 4:6 and 9:10) |
| Gentleness as submission to harm | Chapters 16–17 and Appendix D state that gentleness includes boundaries and that danger requires reporting and safety |
| Health claims | Chapter 22 and Appendix D: prayer and qualified care coexist; illness is not a spiritual failure |
| Aesthetic performance | Chapter 15 distinguishes the heart from the outward appearance (Matthew 23:25; 1 Samuel 16:7) |

## 5. Build verification

| Check | Result |
|---|---|
| Interior PDF | 139 pages, 6 × 9 in |
| Printed TOC page numbers | 41 filled, 0 empty; Preface included |
| EPUB identifier | `soft-life-gods-way-2026` (unique) |
| EPUB duplicate entries | 0 |
| Cover wrap | 12.5630 × 9.2500 in, with barcode zone |
| DOCX | built with real core properties and auto-update TOC |

## 6. Outstanding

1. **Length** — approximately 15,800 words. This is shorter than the 22,000–24,000 words originally planned. The chapters are deliberately tight rather than padded; if a longer trade edition is wanted, the natural places to expand are the composite illustrations and the practice chapters.
2. **ISBN** — none assigned; the back cover has a marked barcode area.
3. **Cover artwork** — the supplied illustration (`cover_source.png`, 1024 × 1536 px) is used. It carries the primary subtitle (option 1) verbatim. The artwork has been upscaled to 1800 × 2700 for a 6 × 9 trim at 300 dpi, but the source detail is limited; a native-resolution file is desirable for a physical print run. The filename also yielded a fourth positioning variant, *"A Joyful Family Journey"*, preserved in `Subtitle_Options.md` but not adopted as the subtitle.
4. **Audience** — written for Christian women, per the editorial decision; options 2 and 3 remain available for broader positioning.

## 7. Presentation audit fixes applied

A critical audit of the rendered proofs found and corrected:

| Defect | Fix |
|---|---|
| Left-hand print pages carried book 1's running header "DIVINE AUTHORITY" | Running header is now config-driven in `build_html()`; book 4 prints "SOFT LIFE GOD'S WAY", book 3 its own title |
| Back-cover author line was clipped | Byline reduced to 8.5 pt with tighter tracking; now fully legible |
| Teaching Notes callouts split across pages, leaving two-line pages | `break-inside: avoid` added to `.callout` in `print.css` |
| EPUB creator used the pen name while DOCX used the legal name | DOCX core author now uses the public author form; the legal name remains in the copyright line |
| Cover wrap PDF had no title/author metadata | Added both |
| EPUB cover JPEG was 1.07 MB | Recompressed to quality 82; EPUB now 846 KB |
| EPUB opened at the Introduction with no title or copyright page | Title page, copyright page and preface added to the EPUB spine |
| HTML keywords were book 1's topic list | Keywords are now config-driven |

All four books were rebuilt after the shared `build.py` and `print.css` changes.

## 8. Verdict

**Ready for a Volume One prelaunch.** The manuscript is Christ-centred, all 106 quotations are verified, the three subtitles are preserved, the safeguards are explicit, and the packaging now builds cleanly. Outstanding production items are the ISBN and a native-resolution cover file.
