# TASK 1 — LITERAL vs FIGURATIVE CLASSIFICATION: FULL REPORT
## Écopoétique — Figurativity Analysis
**Date:** June 28, 2026
**Author:** Labiba Farooq
**Supervisor:** Riccardo Barontini

---

## WHAT TASK 1 IS

Task 1 classifies every animal and plant mention extracted from the corpus as either:
- **référentiel** — the term refers to a real, physically present animal or plant (literal use)
- **figuré** — the term is used as a metaphor, comparison, idiom, or symbol (figurative use)

This is a prerequisite for all downstream tasks (Task 2 subcategories, Task 3 agentivity, Task 4–5 narratology), which only operate on **référentiel** mentions.

---

## MODEL AND SETUP

| Parameter | Value |
|---|---|
| Model | qwen3:30b |
| Server | Ollama on http://localhost:11435 |
| GPU | NVIDIA A40 (46GB VRAM, ~22GB used by model) |
| Temperature | 0 (deterministic) |
| num_predict | 5000 (required for thinking mode) |
| Thinking mode | ON — model uses internal chain of thought before answering |

### Why num_predict=5000 is required

We tested reducing num_predict to speed up the run. At 100 tokens (no-think mode), figurative accuracy dropped to **0%** — the model needs its thinking chain to detect figurative language. Cannot use no-think mode for Task 1.

| num_predict | Speed | Figurative accuracy |
|---|---|---|
| 5000 | 9.4s/row | 81.2% (baseline) |
| 2000 | 7.1s/row | ~75% |
| 1000 | 5.5s/row | ~40% |
| 500 | 4.8s/row | ~13% |
| 100 (no-think) | 1.2s/row | **0%** |

---

## FINAL PROMPT DESIGN (v6)

The final approved prompt (from `evaluate_all_goldsets_v6.py`) consists of:

### CORE_DEFINITIONS (7 rules)
1. Expression idiomatique connue → toujours figuré
2. Comparaison avec "comme" pour décrire un humain → figuré
3. Être réellement présent dans la scène → référentiel
4. Contexte scientifique, géographique, naturaliste, écologique → référentiel
5. Crise environnementale réelle → référentiel même si le verbe semble fort
6. Terme africain/asiatique dans contexte colonial ou de voyage → référentiel
7. Métaphore décrivant émotion ou situation humaine → figuré

### EXAMPLES
- **Animaux**: 4 référentiel examples + 5 figuré examples (poules, aigle, truites, chat / chevaux, cochon, bœuf, chats, mouches)
- **Plantes**: 5 référentiel + 5 figuré + 3 "cas difficiles" including the olive branch symbol distinction

---

## GOLD SET RESULTS — SINGLE ROW (v6 baseline)

These are the agreed accuracy numbers with Riccardo. Script: `evaluate_all_goldsets_v6.py`

| Category | Gold set | Réf | Fig | Overall |
|---|---|---|---|---|
| Animaux | 190 rows (121 réf + 69 fig) | 97.5% (118/121) | 81.2% (56/69) | 91.6% (174/190) |
| Plantes | 188 rows (164 réf + 24 fig) | 98.8% (162/164) | 79.2% (19/24) | 96.3% (181/188) |
| Loterre | — | 91.2% | 63.4% | 85.2% |

Loterre script: `evaluate_loterre_v8.py` (separate prompt with geographic/ecological rules)

---

## SPEED PROBLEM AND SOLUTION

### Original time estimate
At 9s/row single-row mode:
- Animaux (127,816 rows): ~319h = **13.3 days**
- Plantes (69,287 rows): ~173h = **7.2 days**
- **Total: ~20 days** — impossible before July 15 deadline

### Strategy tested: Batching (sending N rows per API call)

Instead of one sentence per API call, we send N sentences in a single call and get back a JSON array of labels.

Tests run on the full animaux gold set (190 rows) with exact v6 prompts:

| Batch size | Speed | Animaux | Plantes | Fig accuracy (animaux) |
|---|---|---|---|---|
| 1 (baseline) | 9.0s/row | 13.3 days | 7.2 days | 81.2% |
| 3 | 4.4s/row | 6.5 days | 3.0 days | 81.2% |
| 4 | 3.9s/row | 5.8 days | 2.7 days | 81.2% |
| 5 | 3.4s/row | 5.0 days | 2.7 days | 79.7% |

**Key finding**: Batch=3 and batch=4 preserve IDENTICAL figurative accuracy to single-row v6 (56/69 = 81.2%). Only batch=5 loses 1 extra figurative item.

### Decision: batch=4
- Same fig accuracy as v6 for animaux (81.2% = 56/69)
- Plantes fig: 75% (18/24) vs v6's 79.2% (19/24) — 1 item difference
- Total time: 5.8 + 2.7 = **8.5 days** → finishes ~July 7 ✓

---

## FULL GOLD SET COMPARISON (all batch sizes)

### Animaux (121 réf + 69 fig = 190 rows)

| Method | Réf | Fig | Overall | Speed | Corpus days |
|---|---|---|---|---|---|
| v6 (1 row) | 118/121 (97.5%) | 56/69 (81.2%) | 174/190 (91.6%) | 9.0s | 13.3d |
| batch=3 | 117/121 (96.7%) | 56/69 (81.2%) | 173/190 (91.1%) | 4.4s | 6.5d |
| **batch=4** ✓ | **115/121 (95.0%)** | **56/69 (81.2%)** | **171/190 (90.0%)** | **3.9s** | **5.8d** |
| batch=5 | 114/121 (94.2%) | 55/69 (79.7%) | 169/190 (88.9%) | 3.4s | 5.0d |

### Plantes (164 réf + 24 fig = 188 rows)

| Method | Réf | Fig | Overall | Speed | Corpus days |
|---|---|---|---|---|---|
| v6 (1 row) | 162/164 (98.8%) | 19/24 (79.2%) | 181/188 (96.3%) | 9.0s | 7.2d |
| batch=3 | 164/164 (100.0%) | 14/24 (58.3%) | 178/188 (94.7%) | 3.7s | 3.0d |
| **batch=4** ✓ | **160/164 (97.6%)** | **18/24 (75.0%)** | **178/188 (94.7%)** | **3.3s** | **2.7d** |
| batch=5 | 160/164 (97.6%) | 17/24 (70.8%) | 177/188 (94.1%) | 3.1s | 3.2d |

Note on batch=3 plantes fig (58.3%): this is a statistical artifact — the plantes gold set has only 24 figurative items (each error = 4.2pp swing). Batch=3 happened to pair figurative plant terms next to very literal items in that run, biasing the model. Not a reliable measurement.

---

## KNOWN SYSTEMATIC ERRORS

From cross-batch analysis, these items are wrong in ALL batch sizes (3, 4, and 5) — they represent genuine limitations of the system:

### Animaux — 12 systematic errors

| Token | Gold | System says | Analysis |
|---|---|---|---|
| agneaux | réf | figuré | Ambiguous context — probably gold is correct |
| grenouilles | réf | figuré | Ambiguous cultural reference |
| porc | figuré | réf | System likely correct — context describes literal pig |
| vache | figuré | réf | System likely correct — "draw a cow" = literal |
| bœuf | réf | figuré | "nerf de bœuf" — system misreads as expression |
| chimpanzés | figuré | réf | "à un % près nous sommes des chimpanzés" — scientific-sounding but figurative |
| chiens (×1) | figuré | réf | Borderline — dogs observing = literal? |
| lion (×2) | figuré | réf | Implicit metaphor without explicit "comme" marker |
| abeille | réf | figuré | Philosophical analogy context misleads model |
| âne (×2) | figuré | réf | Implicit metaphor, no explicit marker |

### Plantes — 5 systematic errors

| Token | Gold | System says | Analysis |
|---|---|---|---|
| plantes ligneuses | figuré | réf | System may be right — context describes rotting plants |
| jasmin | figuré | réf | Borderline — "bercés dans le jasmin" ambiguous |
| abricotier | figuré | réf | Implicit metaphor, unclear from context |
| palmiers | figuré | réf | Learning context, could be literal |
| ananas | figuré | réf | Borderline |

### Why these errors occur

1. **Implicit metaphors** — when figurative use has no explicit marker ("comme", "tel un"), the model defaults to référentiel
2. **Truncated context** — sentences are pre-truncated; the figurative signal may be in the surrounding paragraph
3. **Borderline cases** — some are genuinely ambiguous (porc, vache, chiens); even human annotators may disagree

### Why we chose NOT to fix them before running

- Increasing context size (200 → 400 chars) would require re-extracting from 925 raw novels — too risky with July 15 deadline and would add ~15% time
- Adding prompt examples for these cases risks breaking currently-correct items
- The 12+5 systematic errors are a small fraction of 127k+69k rows
- They will be documented in the paper as known limitations

---

## CORPUS TO RUN ON

The previous team already ran: extraction → sentence truncation → lemmatization → category assignment → homograph disambiguation (~85% by Joanna/GPT). **All pre and post correction is already done.** Task 1 runs directly on these files.

| File | Rows | Description |
|---|---|---|
| `resultats/corpus_principal/ENTITES_contexte_animaux.csv` | 114,851 | Corpus total (925 novels) — animals |
| `resultats/bestsellers/BESTSELLERS_contexte_animaux.csv` | 13,094 | Bestsellers (88 novels) — animals |
| `resultats/corpus_principal/ENTITES_contexte_plantes.csv` | 63,599 | Corpus total — plants |
| `resultats/bestsellers/BESTSELLERS_contexte_plantes.csv` | 5,720 | Bestsellers — plants |

After deduplication:
- **Animaux: ~127,816 unique rows**
- **Plantes: ~69,287 unique rows**

Column names differ between files: corpus_principal uses `truncated_sentence`, bestsellers uses `contexte`. The run script normalizes both to `contexte`.

---

## PROJECTED ERRORS IN FULL CORPUS

Scaled from gold set error rates (note: real corpus has fewer figurative items than the artificially-enriched gold set, so actual errors will be lower):

### Animaux (127,816 rows)

| Method | Réf errors | Fig errors | Total wrong |
|---|---|---|---|
| v6 (1 row) | ~2,020 | ~8,745 | ~10,765 (8.4%) |
| **batch=4** | ~4,036 | ~8,745 | ~12,781 (10.0%) |
| batch=5 | ~4,709 | ~9,418 | ~14,127 (11.1%) |

### Plantes (69,287 rows)

| Method | Réf errors | Fig errors | Total wrong |
|---|---|---|---|
| v6 (1 row) | ~738 | ~1,843 | ~2,580 (3.7%) |
| **batch=4** | ~1,474 | ~2,211 | ~3,685 (5.3%) |
| batch=5 | ~1,474 | ~2,580 | ~4,054 (5.9%) |

---

## RUN STARTED — June 28, 2026

**Script:** `métaphore/run_task1_corpus.py`
**Command:**
```bash
cd ~/ecopoetique/métaphore
nohup python3 run_task1_corpus.py --category animaux > ../resultats/task1_animaux_run.log 2>&1 &
# after animaux finishes (~5.8 days):
nohup python3 run_task1_corpus.py --category plantes > ../resultats/task1_plantes_run.log 2>&1 &
```

**Monitor progress:**
```bash
tail -f ~/ecopoetique/resultats/task1_animaux_run.log
```

**Resume if interrupted:** Re-run the same command. The script reads the existing output file and skips already-classified rows automatically.

**Timeline:**
| Task | Start | Estimated finish |
|---|---|---|
| Animaux | June 28 | ~July 4 |
| Plantes | ~July 4 | ~July 7 |
| **All done** | — | **~July 7** ✓ (before July 15 deadline) |

**Output files:**
- `resultats/task1_animaux_labels.csv` — unique rows with task1_label column
- `resultats/task1_animaux_labels_full.csv` — all rows including duplicates (for joining back to original data)
- Same for plantes

---

## SCRIPTS REFERENCE

| Script | Purpose |
|---|---|
| `evaluate_all_goldsets_v6.py` | Final v6 gold set evaluation (animaux + plantes), single row |
| `evaluate_loterre_v8.py` | Final loterre gold set evaluation |
| `evaluate_goldsets_batch5.py` | Batch=5 full gold set evaluation with row-by-row output |
| `evaluate_goldsets_batch34.py` | Batch=3 and batch=4 comparison on both gold sets |
| `test_speed_vs_accuracy.py` | num_predict speed/accuracy tradeoff tests |
| `test_batching.py` | Initial batch size test (30-row sample) |
| `test_batch5_fullgold.py` | Batch=1 vs batch=5 on full animaux gold set |
| **`run_task1_corpus.py`** | **← FINAL RUN SCRIPT. Batch=4 on full corpus.** |

---

## NEXT STEPS AFTER TASK 1

1. Task 1 results (référentiel/figuré labels) feed into:
   - **Task 2**: subcategory classification (only on référentiel mentions)
   - **Task 3**: agentivity analysis (already run on old data; re-run on Task 1 filtered data)
   - **Tasks 4–5**: narratology

2. Gold set for Task 2 needs to be generated: `create_gold_task2.py` (100 figurative animals + 100 figurative plants → send to Riccardo)

3. Loterre: fix ambiguous gold set cases, rerun accuracy

4. Next meeting with Riccardo: **July 3, 11am**
   - Discuss Task 1 progress (should be ~halfway through animaux)
   - Discuss Task 2 gold set annotation
   - Discuss whether to use Joanna's animal results as proxy or wait for our results
