# TASK 4.5 — COMPARE-TARGET CLASSIFICATION: FULL REPORT
## Écopoétique — Figurativity Analysis
**Date:** 2026-10-30
**Author:** Labiba Farooq
**Supervisor:** Riccardo Barontini

---

## WHAT TASK 4.5 IS

For every figurative mention Task 2 has already categorized, Task 4.5 asks: what kind of thing is the metaphor's vehicle actually standing in for? 6 categories, defined by Riccardo directly (`métaphore/Catégories analyse comparés.docx`):

- **CH** — characteristics/behavior (e.g. "rat" used for someone's sneaky personality)
- **P** — physical (the person's physical body/dimension specifically)
- **NH** — non-human (another animal/plant/thing, not a human)
- **O** — object
- **E** — entity/place (e.g. comparing an island to a rat)
- **A** — abstract (emotions, situations)

**Riccardo's own framing of the real test, verbatim**: "the objective of the task is not to determine which kind of concept the metaphor is designating but which kind of entity the metaphor is referring to." A concrete distinction he gave: "battre en retraite" (to retreat) bound to a character's physical body → **P**; the same phrase applied to their *behavior* → **CH**.

Task 4.5 is the final step feeding off Task 1 (literal/figurative) and Task 2 (metaphor subcategory) — it needs both as input.

---

## THE HONEST ACCURACY NUMBER: 76.3%, NOT 81.8%

Same structural issue as Task 2, same underlying gold file: this gold set has a pre-existing dev/test split (`comparison/task45_dev_test_split.json`: 78 dev rows, 76 test rows) that was previously used to tune earlier iterations. Scored on the honest partition:

- **Raw (all 154 usable rows): 81.8% (126/154)**
- **Dev (78 rows, tuning-exposed): 87.2% (68/78)**
- **Test (76 rows, genuinely untouched): 76.3% (58/76)** ← **this is the number to quote**

All three numbers independently re-verified on 2026-10-30 directly from `resultats_task45_compare_category.csv` (not taken on trust from an earlier session's claim).

Script: `comparison/run_task45_compare_category.py`, reading `métaphore/gold_task2_task45_CURRENT.csv` (200 rows total; 16 X-skipped, 30 legitimately blank/N-A for this column, leaving 154 usable).

---

## A genuinely messy schema history (useful context if Riccardo asks why this took months)

The category definitions changed substantially across 5 email exchanges between 2026-07-08 and 2026-09-17:

1. **Jul 8**: Riccardo sends the original written definitions (O/NH/E/CH/A/P).
2. **Jul 10**: a major reframe — he clarifies the task isn't "what concept does this describe" but "what entity does this literally refer to," using a worked example (a rat metaphor for a person → CH, the same animal for an island → E).
3. **Jul 10 (same day)**: a further split — whether a body-related metaphor points to someone's physical body (P) or their behavior (CH) depends on which the sentence's extended context actually supports.
4. **Sep 17**: one specific gold row ("ours en peluche," a teddy bear) didn't fit any of the 6 categories. Riccardo's own resolution revealed a **third scoring convention**: a row can have a real Task 2 subcategory filled in while having literally `X` (not blank) in the Task 4.5 column, meaning "this is figurative language, but there's no comparé target for this specific question." This is distinct from rows where both columns are blank (meaning "not actually figurative, a Task 1 false positive").

**This third convention is implemented correctly in the current scoring script** — worth confirming this explicitly with Riccardo since it's easy to get wrong.

---

## WHAT'S DONE AND WHAT'S NOT

**Done**: gold-set validation (76.3% honest), using the main v1 script.

**Built but never run**: `run_task45_compare_category_v2_physical_psych.py` — a variant built specifically around the physical-vs-psychological distinction (item 3 above). No output file exists for it anywhere. Worth running and comparing against v1 before considering the gold-set work fully closed.

**Not cross-compared**: a separate retrieval-based few-shot variant (`run_task45_retrieval_fewshot.py`) and an embeddings-based variant (`embed_task45_examples.py`) both exist but were never benchmarked against the main script to see if either does better.

**Full-corpus run: genuinely blocked, not just stalled.** Task 4.5 needs each real corpus mention's Task 2 subcategory as input — that only exists for the 184 rows in the Task 2 gold set so far. Task 2's own full-corpus run is itself stalled at ~35% (see `task2_report.md`). Nothing to run at scale until that unblocks.

---

## WHERE THE FILES LIVE

**Production scripts (`comparison/`):**
- `run_task45_compare_category.py` — the validated technique
- `run_task45_compare_category_v2_physical_psych.py` — built, never run
- `run_task45_retrieval_fewshot.py` — alternate variant, never cross-compared
- `embed_task45_examples.py` — embeddings variant support

**Gold set and definitions:**
- `métaphore/gold_task2_task45_CURRENT.csv` — the file the script actually reads
- `métaphore/Catégories analyse comparés.docx` — Riccardo's original category definitions
- `comparison/task45_dev_test_split.json` — the honest dev/test partition

**Results:**
- `comparison/resultats_task45_compare_category.csv` — the validated 154-row gold-set result

## OPEN ITEMS

- Run and compare the v2 (physical/psychological) variant against v1.
- Cross-compare the retrieval-fewshot and embeddings variants against the main script.
- Full-corpus run blocked on Task 2's full-corpus run finishing.
- Confirm with Riccardo that the "X in Task 4.5 column, real subcategory in Task 2 column" scoring convention is implemented as he intended.
