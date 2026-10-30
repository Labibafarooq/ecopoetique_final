# TASK 2 (METAPHOR SUBCATEGORY CLASSIFICATION) — COMPLETE RESEARCH HISTORY
**Sourced from**: direct re-computation of every technique's actual result file (`métaphore/` and `métaphore/v2/`), not taken from memory summaries, on 2026-10-30. Every score below was independently recomputed from the real CSV output at the time of writing. Where a file's current score differs from an earlier memory note, the current, freshly-recomputed number is the one reported, and the discrepancy is flagged rather than silently resolved.

---

## What Task 2 is

For every mention Task 1 classified as figurative, assign one of 19 structural metaphor subcategories (16 original + `COUL`/`LOC_IDIOM`/`IMAG`, added later by Riccardo). The pipeline is a hybrid cascade: a rule layer and a spaCy dependency-parse check resolve the easy ~35% of cases for free; the remaining ~65% go to an LLM call.

## Baseline

**Original production** (decision-tree prompt, no few-shot examples, qwen3:30b): **71.7% (132/184)**. This is the number every subsequent technique had to beat.

## Techniques tried, in order, with real verified scores

| # | Technique | Score | Verdict |
|---|---|---|---|
| 1 | TF-IDF + LinearSVC (5-fold CV) | **26.1%** | Rejected — surface lexical features alone are far too weak for this task |
| 1b | TF-IDF + Logistic Regression (5-fold CV) | **25.0%** | Rejected, same reason |
| 2 | Smaller model (qwen2.5:7b, 20-row smoke test) | **20.0% (4/20)** | Rejected without a full run — model too weak, not worth the compute to confirm at scale |
| 3 | Dependency-feature decomposition (rule/spaCy/LLM breakdown by syntactic feature) | **43.5% (80/184)** | Rejected — a real regression below baseline |
| 4 | Coarse-to-fine (classify broad category first, then narrow) | **56.5% (104/184)** | Rejected — a real regression below baseline |
| 5 | Context-window (expand the surrounding text shown to the model) | **73.4% (135/184)** | A real, modest improvement over baseline, but not pursued further once retrieval-fewshot (below) beat it |
| 6 | Static few-shot (fixed example set, deduped) | **75.0% (138/184)** | Better than context-window, but still a fixed example set — superseded by retrieval-based few-shot |
| 7 | Self-consistency majority-vote (n=5 samples, temp=0.7, on 5 specific rows observed flipping between identical-code runs) | Diagnostic, not a full-corpus score | Confirmed real non-determinism exists in the LLM's answers on borderline rows — informed later work, not itself a deployed fix |
| 8 | **Retrieval-based few-shot, k=3** (retrieve 3 most similar examples from a curated bank per row) | **76.1% (140/184)** | Real improvement — first technique to establish the retrieval approach works |
| 9 | **Retrieval-based few-shot, k=4** | **76.6% (141/184)** | Better than k=3 — this became the credited production technique |
| 10 | Expanded bank (23→28 examples) | **75.5% (139/184)** | **A regression** — and a real process bug: this experiment edited the k=4 script in place instead of using a copy, meaning the credited 76.6% result briefly stopped being reproducible from the script on disk. Caught and reverted; the k=4 script was restored to its original 23-example bank, re-verified via AST-level parsing (not just visual inspection) to confirm exactly 23 entries with zero gold-set leakage. **Lesson applied project-wide afterward: never edit a credited-result script in place, always test variations in a copy.** |
| 11 | Idiom-lexicon fix (3 missing idiom variants added to a 69-entry lexicon, each addition checked for zero new false fires before trusting it) | **77.7% (143/184) raw** | Real, genuine improvement from the lexicon fix alone — but see the critical caveat below before quoting this number |
| 12 | Retrieval-fewshot + idiomfix, FINAL (current production state, re-verified 2026-10-30) | **78.3% (144/184) raw** | Current state of the credited script — see honest scoring below |

## The critical finding: the honest accuracy is 74.4%, not 78.3% or 77.7%

This gold set has a genuine pre-existing dev/test split (`métaphore/task2_dev_test_split.json`: 94 dev rows, 90 test rows) that was used in past sessions to tune the rule layer's logic — a real form of leakage on the dev side, even though no row's literal text was ever copied into a prompt. Scored on the current FINAL file (re-verified 2026-10-30):

- **Raw (all 184 rows): 78.3% (144/184)**
- **Dev (94 rows, tuning-exposed): 81.9% (77/94)**
- **Test (90 rows, genuinely untouched): 74.4% (67/90)** ← **the number that has stayed stable and should always be quoted**

Note: the dev and raw figures have crept upward slightly since this was first computed (76.6%→78.3% raw, 80.9%→81.9% dev) as small fixes accumulated — but **the test score has not moved at all, 67/90 = 74.4%, across every version checked.** This is itself a reassuring sign: whatever small improvements have landed, they've landed on the already-tuning-exposed dev side, not genuinely improved generalization — so 74.4% remains the correct, stable number to quote.

**A separate, inflated figure that must never be used**: 2 self-proposed gold-label corrections (ids 82 "oignons", 87 "blé") were sent to Riccardo and **explicitly rejected** (2026-10-26) with real reasoning in both cases — he confirmed the *original* labels (META_APP for oignons, META_NOM for blé) were correct, not the proposed META_QUAL. A version of the result file that counted these corrections as right would show 77.7%; this is not a valid number and should not be cited.

## Full-corpus run

Launched 2026-10-25 across 2 GPUs, targeting ~44,781 figurative-mention candidates. Crashed once from an uncapped-thread explosion (no BLAS/OMP caps set on parallel CPU+GPU hybrid processes on a 256-core shared machine), fixed and relaunched. **Currently stalled at ~35% (15,901/44,781 rows)** — no process running, needs a manual restart to finish.

## Open items

- Full-corpus run needs restarting and finishing.
- A fresh 30-row unlabeled sample (`fresh_sample_check.csv`) was pulled for a face-validity check but never actually read/judged by a human.
- No materially tighter accuracy number is possible without new human-annotated gold data — a statistical limit (95% CI for 67/90 is roughly 65-83%), not an engineering gap.
