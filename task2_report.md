# TASK 2 — METAPHOR SUBCATEGORY CLASSIFICATION: FULL REPORT
## Écopoétique — Figurativity Analysis
**Date:** 2026-10-30
**Author:** Labiba Farooq
**Supervisor:** Riccardo Barontini

---

## WHAT TASK 2 IS

For every mention Task 1 classified as **figuré** (figurative), Task 2 assigns one of 19 structural metaphor subcategories (the original 16 from Riccardo's reference table, plus 3 later additions: `COUL`, `LOC_IDIOM`, `IMAG`), covering things like nominal metaphor (`META_NOM`), qualitative metaphor (`META_QUAL`), apposition (`META_APP`), frozen idioms (`LOC_IDIOM`), and comparison/simile (`COMP_SIM`). The full category list and definitions are in `schema_analogies_vivant_complet_0807.csv`.

Task 2 is a prerequisite for Task 4.5 (compare-target classification), which needs each mention's Task 2 subcategory as input.

---

## THE HONEST ACCURACY NUMBER: 74.4%, NOT 78.3%

The pipeline uses a hybrid rule → spaCy → LLM cascade: most mentions resolve for free via a rule layer or a spaCy dependency-parse check; only ambiguous cases (about 65% of the gold set) go to an LLM call (qwen3:30b, retrieval-based few-shot, k=4 examples drawn from a 23-example canonical bank).

On the 184-row gold set (of 200 total, 16 held back for other purposes), the current production file scores (re-verified directly 2026-10-30):
- **Raw: 78.3% (144/184)**
- **With 2 self-proposed gold-label corrections counted as right: 77.7% (143/184) on an earlier version of this file** — **do not use this number, see below.**

This project has a pre-existing, genuine dev/test split (`task2_dev_test_split.json`: 94 dev rows, 90 test rows). The dev rows had been looked at repeatedly in past sessions to tune the rule layer's logic — a real form of leakage, even though no row's literal text was copied anywhere. Scored on the honest partition (re-verified 2026-10-30):
- **Dev (94 rows, tuning-exposed): 81.9% (77/94)**
- **Test (90 rows, genuinely untouched): 74.4% (67/90)** ← **this is the number to quote — and notably, it has not moved at all across every version of this file checked, even as the raw/dev figures crept up slightly from small fixes. Full technique-by-technique history in `TASK2_RESEARCH_HISTORY_COMPLETE.md`.**

**The 2 proposed gold corrections were sent to Riccardo and rejected (2026-10-26)**, with real reasoning in both cases:
- id=82 "oignons" → he confirmed **META_APP**, not META_QUAL (the whole phrase stands in apposition to the referent as a unit-level metaphor — not an internal N1-de-N2 metaphorization).
- id=87 "blé" → he confirmed **META_NOM** (matching the original label), not META_QUAL (neither word inside "épi de blé" is itself metaphorizing; the metaphor is at the image level, not the internal structure).

Both rows are correctly counted wrong under the current model. The genuinely real improvement — from an idiom-lexicon fix, independent of the rejected gold corrections — is **72.2% → 74.4%**.

At n=90, the 95% confidence interval for 67/90 is roughly 65-83% — real sampling uncertainty exists on top of everything above. A materially tighter number would need new human-annotated gold data.

---

## WHERE THE TECHNIQUE CAME FROM

~8 earlier approaches were tried and failed to beat the original 71.7% production baseline before the retrieval-based few-shot technique worked: static few-shot (3 variants), TF-IDF, dependency-features, coarse-to-fine, context-window, majority-vote. Retrieval-based few-shot (retrieving the 4 most similar examples from a curated 23-example bank for each new case, rather than a fixed example set) was the first to genuinely beat the ceiling.

**A real bug was caught and fixed during validation**: the credited script had been edited in place during a later, failed bank-expansion experiment (23→28 examples), meaning it no longer reproduced its own validated result on disk. Restored to the original 23-example bank, re-confirmed via code-level parsing (not just visual inspection) that it's exactly 23 entries with zero gold-set leakage, checked against all 200 rows.

**Lesson applied going forward**: never edit a credited-result script in place — always test variations in a copy.

---

## FULL-CORPUS RUN — IN PROGRESS, CURRENTLY STALLED

Launched 2026-10-25, split across 2 GPUs (`--half 1`/`--half 2`), targeting ~44,781 figurative-mention candidates (the full corpus minus the 184 gold rows already scored). Estimated ~5 days wall-clock at the validated rate (~65% of rows need an LLM call, ~10-15 sec/call).

**Current state, checked 2026-10-30**: both halves have stalled.
- `resultats_task2_full_corpus_half1.csv`: 8,895 rows (last touched 2026-10-28)
- `resultats_task2_full_corpus_half2.csv`: 7,006 rows (last touched 2026-10-27)
- **15,901 of ~44,781 rows done (~35.5%)**. No process currently running. Needs to be restarted to finish.

One incident during this run: the first launch crashed the shared server (no BLAS/OMP thread caps set on 2 parallel CPU+GPU hybrid processes, pushing system thread count past 998 on a 256-core machine). Fixed by setting `OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2` before each launch, and relaunching — this fix should be reapplied when restarting.

A separate face-validity check (`fresh_sample_check.csv`, 30 random unlabeled corpus rows, not a rigorous score) was run to sanity-check the technique isn't doing anything obviously broken at real scale — predictions looked plausible on inspection but were never formally reviewed row-by-row.

---

## WHERE THE FILES LIVE

**Production scripts:**
- `métaphore/v2/run_retrieval_idiomfix_FINAL_184.py` — the validated 74.4% technique
- `métaphore/v2/run_task2_full_corpus.py` — full-corpus adaptation
- `métaphore/v2/spacy_syntax_classifier.py` — rule/spaCy prefilter
- `métaphore/run_task2_subcategories.py` — shared module

**Gold set and schema:**
- `métaphore/v2/gold_task2_task45_CURRENT.csv` — the correct, Riccardo-validated gold file (use this one, not `gold_task2_task45_v2corrected.csv`, which contains 2 corrections he rejected)
- `métaphore/schema_analogies_vivant_complet_0807.csv` — the 19-category definitions
- `task2_dev_test_split.json` — the honest dev/test partition

**Results:**
- `métaphore/v2/resultats_task2_retrieval_idiomfix_FINAL_184.csv` — the validated 184-row gold-set result
- `métaphore/v2/resultats_task2_full_corpus_half1.csv` + `half2.csv` — partial full-corpus output, stalled at ~35%
- `métaphore/v2/fresh_sample_check.csv` — the unlabeled face-validity sample

## OPEN ITEMS

- Full-corpus run needs restarting (and finishing) — the single biggest open piece, same situation as Task 1's Loterre run.
- `fresh_sample_check.csv`'s 30 rows were never actually read and judged for plausibility by a human — that review is still outstanding.
- No materially tighter accuracy number is possible without new human-annotated gold data (statistical, not an engineering gap).
