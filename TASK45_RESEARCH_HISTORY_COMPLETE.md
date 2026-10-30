# TASK 4.5 (COMPARE-TARGET CLASSIFICATION) — COMPLETE RESEARCH HISTORY
**Sourced from**: the live memory store's email-chronology record (`project_email_task2_task45_schema_evolution.md`), direct inspection of `comparison/run_task45_compare_category.py` and its v2 variant, direct re-computation of every result file on 2026-10-30.

---

## What Task 4.5 is

For every figurative mention Task 2 has categorized, classify what kind of entity the metaphor's vehicle is actually standing in for: **CH** (characteristics/behavior), **P** (physical body/dimension), **NH** (non-human), **O** (object), **E** (entity/place), **A** (abstract). Defined by Riccardo in `métaphore/Catégories analyse comparés.docx`.

## The schema evolution — 5 email exchanges, July–September 2026

The category definitions and the precise test for applying them changed substantially over time, in a way worth knowing before showing Riccardo anything, since it explains why the "right" answer on some gold rows isn't obvious from the category names alone:

1. **2026-07-08**: Riccardo sends the original written definitions.
2. **2026-07-10 (first reframe)**: he clarifies the real test isn't "what concept does the metaphor describe" but "what entity does it literally refer to" — worked example: "rat" applied to a person → CH; the same animal applied to an island → E.
3. **2026-07-10 (second reframe, same day)**: when the target is a person, a further split is needed — does the comparison point to their physical body/action (→ CH) or their character/behavior (→ P)? Verbatim example: *"battre en retraite"* (to retreat) bound to someone's physical body → CH; the same phrase describing someone's *behavior* (cowardice) → P. A second worked example from this exchange: *"Pierre Castaneda se comporte comme un chacal"* (rapacity) → P, because the referent is his conduct, not his body.
4. **2026-09-17**: a specific row ("ours en peluche," a teddy bear) didn't fit any of the 6 categories. Riccardo's resolution revealed a third scoring convention: a row can have a real Task 2 subcategory filled in while having literally `X` (not blank) in the Task 4.5 column, meaning "this is figurative language, but there is no comparé target to classify here." Distinct from rows where both columns are blank (a Task 1 false positive, not actually figurative at all).

## A real, confirmed defect found in the current production script

**v1** (`comparison/run_task45_compare_category.py`, the script behind every validated score below) was checked directly against the schema history above. Its current CH/P rule still says, verbatim: *"le trait illustré (lâcheté) est psychologique, MAIS la cible est une personne → CH, PAS P. Ne classe jamais par le domaine du trait"* — i.e., the crude pre-refinement rule ("target = person, always CH"), not the physical-vs-behavioral split Riccardo explicitly gave in item 3 above.

**v2** (`comparison/run_task45_compare_category_v2_physical_psych.py`) was built the same day (2026-07-10) specifically to encode the correct refinement, using the exact Pierre Castaneda example. Its own docstring states it was **never tested** — GPU access froze for ~12 days the day it was written, and it was never revisited afterward, through any of the later schema rewrites (Sep 17, Oct 13) that touched other parts of the pipeline.

**Status as of 2026-10-30**: a test run of v2 against the current gold set was started but interrupted (stopped deliberately to free the GPU queue for a higher-priority task) before producing a result. It remains genuinely untested. Given v1 is confirmed to use a rule Riccardo explicitly said was insufficient, **v1's current accuracy number likely has some rows wrong in a specific, already-known way** — this is not a speculative improvement to chase, it's closing a confirmed gap between the code and what was actually asked for.

## v1's validated accuracy

On the 154 usable rows (of 200 total; 16 X-skipped, 30 legitimately blank/N-A):

- **Raw: 81.8% (126/154)**
- **Dev (78 rows, tuning-exposed): 87.2% (68/78)**
- **Test (76 rows, genuinely untouched): 76.3% (58/76)** ← the number to quote

All three independently re-verified directly from `comparison/resultats_task45_compare_category.csv` on 2026-10-30.

## Alternate variants tried

| Variant | Result | Verdict |
|---|---|---|
| Retrieval-based few-shot (`run_task45_retrieval_fewshot.py`) | **65.8% (50/76) on the test set** | Tested, confirmed worse than v1's 76.3% — this result exists in `task45_retrieval_test_log.txt` but was never written up anywhere until this document |
| Embeddings-based (`embed_task45_examples.py`) | Not tested as a classifier | Only the embedding-building step (`task45_embeddings.npy` + metadata) was ever run; no scoring attempt exists |
| v2, physical/psychological fix | Not yet scored | Built 2026-07-10, genuinely untested for ~3.5 months, test run started 2026-10-30 but interrupted before completion |

## Full-corpus run

**Genuinely blocked, not stalled**: Task 4.5 needs each real corpus mention's Task 2 subcategory as input, which only exists for the 184-row Task 2 gold set so far (Task 2's own full-corpus run is itself stalled at ~35%, see `TASK2_RESEARCH_HISTORY_COMPLETE.md`). Nothing to run at scale until that unblocks.

## Open items

- Finish testing v2 (physical/psychological fix) against the gold set — this is the single most important open item, since it addresses a confirmed, not speculative, divergence from Riccardo's own stated rule.
- Score the embeddings variant as an actual classifier.
- Full-corpus run blocked on Task 2's full-corpus run finishing.
- Confirm with Riccardo that the "X in Task 4.5 column, real subcategory in Task 2 column" scoring convention (the "ours en peluche" case) is implemented as he intended — it's coded correctly as far as could be verified, but was never explicitly confirmed back to him.
