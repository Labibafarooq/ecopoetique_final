# TASK 1 — LITERAL vs FIGURATIVE CLASSIFICATION: FINAL RESULTS
## Écopoétique — Figurativity Analysis
**Date:** 2026-07-10
**Author:** Labiba Farooq
**Supervisor:** Riccardo Barontini
**Model:** qwen3:30b (Ollama, batch size 4), thinking mode ON

Task 1 classifies every animal/plant mention extracted from the corpus as either:
- **référentiel** — the term refers to a real, physically present animal or plant (literal use)
- **figuré** — the term is used as a metaphor, comparison, idiom, personification, or symbol

This supersedes the earlier `task1_report.md` (2026-06-28), which predates the plantes run finishing.

---

## 1. GOLD-SET ACCURACY (hand-annotated by Riccardo, consensus-labeled)

Three separate gold sets exist for this task. Accuracy computed by matching each gold row (by fichier + token_lexique + contexte) against the actual production output file.

### 1a. Raw accuracy, gold labels as originally annotated

| Gold set | File | Usable rows (excl. X/?) | Correct | Accuracy |
|---|---|---|---|---|
| **Animaux** | `métaphore/GOLD_litteralite_animaux.csv` | 171 matched / 190 usable (19 not found in output — needs checking) | 154 | **90.1%** |
| **Plantes** | `métaphore/GOLD_litteralite_plantes_RB.csv` | 186 matched / 188 usable (2 not found) | 180 | **96.8%** |
| **Loterre** (mixed animal/plant/natural-element terms, broader validation set) | `métaphore/GOLD_litteralite_loterre__RB.csv` | 189 | 161 | **85.2%** (from `eval_loterre_v8_results.csv`, last run 2026-06-25) |

### 1b. Per-class breakdown (référentiel vs. figuré), raw gold labels

| Gold set | Référentiel accuracy | Figuré accuracy |
|---|---|---|
| **Animaux** | 105/109 = 96.3% | 49/62 = 79.0% |
| **Plantes** | 161/162 = 99.4% | 19/24 = 79.2% |
| **Loterre** | 135/148 = 91.2% | 26/41 = 63.4% |

All three sets show the same pattern: référentiel accuracy is near-ceiling, figuré accuracy is markedly weaker — the model reliably recognizes literal uses but is noticeably worse at catching genuine figurative ones.

### 1c. Manual audit of every figuré miss — some are gold-labeling errors, not model errors

I manually read all 33 rows across the three gold sets where gold=figuré but the model predicted référentiel (13 animaux, 5 plantes, 15 loterre), full context, against the task's own définitions. Verdict: **13 of the 33 are gold-set mislabels** (the model's référentiel call was actually correct), and 4 more are genuine borderline judgment calls (not confidently one way or the other):

| Gold set | Wrong (model vs. gold) | Confirmed gold mislabel (should be référentiel) | Borderline (unresolved) | Genuinely figuré, model missed it |
|---|---|---|---|---|
| **Animaux** | 13 | 3 — chiens, pattes de lion ×2 | 1 — porc | 9 |
| **Plantes** | 5 | 3 — jasmin, palmiers, ananas | 1 — abricotier | 1 |
| **Loterre** | 15 | 7 — forêt, mers, océan, lac ×2, plage, animaux | 2 — désert, incendie | 6 |
| **Total** | 33 | **13** | **4** | 16 |

The confirmed mislabels cluster around a few recognizable patterns: real geographic features used as literal reference points or in literal comparisons (océan, lac, mers, forêt), literal object-category names (jouets de plage), and fixed material/design terms (pattes de lion — consistent with the "boiserie chêne" precedent already confirmed référentiel elsewhere in this corpus).

### 1d. Corrected gold-set accuracy (13 confirmed mislabels reclassified figuré → référentiel)

The 4 borderline rows (porc, abricotier, désert, incendie) were left as originally labeled — only the 13 confirmed mislabels were corrected.

| Gold set | Référentiel | Figuré | Overall |
|---|---|---|---|
| **Animaux** | 108/112 = **96.4%** | 49/59 = **83.1%** | 157/171 = **91.8%** |
| **Plantes** | 164/165 = **99.4%** | 19/21 = **90.5%** | 183/186 = **98.4%** |
| **Loterre** | 142/155 = **91.6%** | 26/34 = **76.5%** | 168/189 = **88.9%** |

Plantes gets the biggest lift (79.2% → 90.5% figuré accuracy) since 3 of its 5 errors were gold mislabels. Loterre improves the most in absolute terms (63.4% → 76.5%) but remains the weakest set even after correction — a genuinely harder benchmark, not just a mislabeling artifact.

**Note on Loterre:** this gold set was used during prompt development (v7/v8 iterations) with its own evaluation script (`evaluate_loterre_v8.py`), which uses a slightly different prompt build than the current production script (`run_task1_corpus.py`, "exact v6 prompts"). It's the closest available benchmark for this set but wasn't re-run against the current v6 production prompt — worth a fresh run if an exact apples-to-apples number is needed.

**Recommendation before showing Riccardo:** present the 13 confirmed mislabels and the 4 borderline cases as two separate tiers, not folded into one number — the borderline cases would likely benefit from a second annotator opinion.

---

## 2. FULL-CORPUS RESULTS (actual production run, all 925 novels + bestsellers)

| Category | Total rows | Référentiel | Figuré | % Figuré |
|---|---|---|---|---|
| **Animaux** | 127,935 | 89,675 | 38,260 | **29.9%** |
| **Plantes** | 69,468 | 59,967 | 9,501 | **13.7%** |

Plantes' lower figuré rate is *not* a bug — it matches the plantes gold set's own ratio (12.8% figuré, 188 rows), so it reflects a real pattern in the corpus: animals are used figuratively/idiomatically far more often than plants in this collection of French novels.

**Plantes retry — now complete.** Both retry passes finished: retry 1 resolved 376 of 444 first-failed rows, retry 2 resolved 36 of the remaining 68. **32 rows are still unresolved** after both passes (logged in `task1_plantes_failed_keys_v3.tsv`, defaulted to référentiel) — negligible (0.05% of 69,468 total rows).

---

## 3. MANUAL SPOT-CHECK — 100 RANDOM SAMPLES PER CATEGORY (50 figuré + 50 référentiel each)

In addition to the gold-set accuracy above, I pulled 100 random rows from each category's actual output (stratified: 50 labeled figuré + 50 labeled référentiel, seeded random sample) and manually judged each one against the task's own définitions/règles, independent of the gold sets. Results:

| Category | Figuré sample clean | Référentiel sample clean | Combined |
|---|---|---|---|
| **Plantes** | 43/50 (86%) | 49/50 (98%) | **92/100 (92%)** |
| **Animaux** | 45/50 (90%) | 45/50 (90%) | **90/100 (90%)** |

Both numbers land close to the gold-set accuracy figures above (96.8% / 90.1%), which cross-validates the gold-set results — the errors aren't random noise, they're small and consistent.

**Recurring error patterns found in the manual check:**
1. **Homograph collisions** — a word that matches the animal/plant lexicon but means something else entirely in context (e.g. "grenadier" = soldier's gait, not a pomegranate tree; "oedipe" = Oedipus complex, not the tamarin monkey).
2. **Representations/images of animals inconsistently handled** — a teddy bear ("ours en peluche") was correctly scored figuré (a representation, not the real thing — consistent with Riccardo's IMAG ruling from the Task 2 meeting), but a glass figurine of a lamb, a painting of a cow, and a photograph of a deer were all scored référentiel instead. This is a real, fixable inconsistency, not just occasional noise — worth flagging to Riccardo.
3. **Literal/scientific-toned statements wrongly flagged as figuré** — e.g. a "fact" about grapefruit being a hybrid of orange and lemon, or a stereotype about chickpea consumption — these are literal statements, not metaphors, but got the figuré label.
4. **Real trees serving a symbolic/ceremonial purpose** (e.g. young poplars placed at a memorial) sometimes mislabeled figuré even though the trees are physically present in the scene — per the task's own rule 3, physical presence should win.

---

## 4. WHERE THE FILES LIVE

**Production script:** `métaphore/run_task1_corpus.py` (+ `run_task1_corpus_throttled.py` for GPU-sharing scenarios)

**Final label outputs (the actual results):**
- `resultats/task1_animaux_labels.csv` — 127,935 rows, tab-delimited (fichier, token_lexique, contexte, lemme, categorie, task1_label)
- `resultats/task1_plantes_labels.csv` — 69,468 rows, same format (backup before last patch: `task1_plantes_labels.csv.bak_before_retry_patch`)

**Failed-batch tracking (plantes):**
- `resultats/task1_plantes_failed_keys.tsv` (first pass, 444 unresolved rows going into retry 1)
- `resultats/task1_plantes_failed_keys_v2.tsv` (68 rows still unresolved after retry 1, going into retry 2)
- `resultats/task1_plantes_failed_keys_v3.tsv` (will contain anything still unresolved after retry 2, in progress)
- Retry scripts: `morphosyntaxe/retry_plantes.py`, `morphosyntaxe/retry_plantes_v2.py`
- Retry logs: `resultats/task1_plantes_retry.log`, `resultats/task1_plantes_retry_v2.log`, watcher log `resultats/task1_plantes_retry_watcher.log`

**Gold sets:**
- `métaphore/GOLD_litteralite_animaux.csv`
- `métaphore/GOLD_litteralite_plantes_RB.csv`
- `métaphore/GOLD_litteralite_loterre__RB.csv` (+ non-RB draft version `GOLD_litteralite_loterre.csv`)
- Loterre evaluation script/output: `métaphore/evaluate_loterre_v8.py`, `métaphore/eval_loterre_v8_results.csv`

**Run logs (production):**
- `resultats/task1_plantes_run.log` (19.8h total runtime, finished 2026-07-10 07:28 UTC)
- Animaux run log — done 2026-07-05, see `PROJECT_DOCUMENTATION.md` for that run's history.

---

## 5. OPEN ITEMS

- 19 animaux gold rows and 2 plantes gold rows couldn't be matched to the production output by exact key — worth a quick check (could be text-normalization differences, e.g. curly quotes, or rows from a corpus version predating the last retry patch).
- The representation/image-of-an-animal inconsistency (§3, point 2) is worth a deliberate fix pass — right now the model's handling of "is a painted/photographed/figurine animal référentiel or figuré" is not consistent, even though Riccardo already gave an explicit ruling on this exact question for Task 2's IMAG category.
- Loterre's 85.2%/88.9% (corrected) is from the v8 prompt iteration, not a fresh run against the current production v6 prompt — re-run if an exact current number is needed.
- 4 borderline gold rows (porc, abricotier, désert, incendie — §1c) need a second annotator opinion before being counted either way.
- Plantes retry is now fully complete — 32 rows remain permanently unresolved in `task1_plantes_failed_keys_v3.tsv` (0.05% of corpus), defaulted to référentiel.
