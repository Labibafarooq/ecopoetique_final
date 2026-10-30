# TASK 3 — AGENTIVITY ANALYSIS: FULL REPORT
## Écopoétique — Morphosyntactic Analysis
**Date:** June 22, 2026 (document started) — **last updated 2026-10-30**
**Author:** Labiba Farooq
**Supervisor:** Riccardo Barontini

---

## STATUS AS OF 2026-10-30 — READ THIS FIRST

This document is a chronological working log, not a single snapshot — sections below from June/July describe problems and gaps that were real **at the time they were written**, and are superseded by later "UPDATE" sections further down. If a number or status below contradicts something later in the document, **the latest dated UPDATE section is always the correct one.**

**Everything in Task 3 is now complete.** Final numbers:

| | Active agent | Passive | Object | Gender (humans only) | N |
|---|---|---|---|---|---|
| Humans | 37.6% | 1.0% | 13.0% | 55.4% masc / 28.5% fém / **16.1% undetermined** | 255,227 |
| Animals (référentiel) | 23.9% | 0.8% | 21.5% | — | 88,859 |
| Plants (référentiel) | 11.1% | 0.4% | 15.4% | — | 58,637 |
| Animals (figuratif) | 16.0% | 0.3% | 13.4% | — | 39,791 |
| Plants (figuratif) | 12.0% | 0.3% | 11.6% | — | 9,351 |

Plus a separate Prix du roman d'écologie (47-novel) subcorpus breakout — see the final UPDATE section at the bottom of this document.

**The "25.9% undetermined gender" figure quoted several times below is outdated** — it was fixed on 2026-10-22 (see "UPDATE — 2026-10-22" further down); the current, correct figure is **16.1%**.

---

## RESEARCH HYPOTHESIS

> Are animals and plants more passive agents compared to humans in contemporary French novels?

The goal is to statistically demonstrate, across the full corpus (925 novels), whether non-human entities (animals, plants) are represented less actively than human characters — and if so, to what extent. The analysis also distinguishes male vs female human characters.

---

## STARTING DATA

### Files already existing (created by previous team, available on GitLab)

| File | Description | Rows |
|---|---|---|
| `resultats/corpus_principal/ENTITES_TOTAL.csv` | All entities extracted from corpus | 317,646 |
| `morphosyntaxe/dépendants_ANIMAUX.csv` | Syntactic dependencies for animals (all) | 126,201 |
| `morphosyntaxe/dépendants_PLANTES.csv` | Syntactic dependencies for plants (all) | 68,920 |
| `morphosyntaxe/dépendants_animaux_référentiels.csv` | Referential animals only (filtered) | 106,410 |
| `morphosyntaxe/analyse_dependances.py` | Analysis script with Agent/Object/Passive classification | — |

### Structure of dependency files
Columns: `fichier | token_lexique | truncated_sentence | lemme | categorie | tête | dépendants | tête_de_tête`

The `tête` column contains the syntactic head of the token and its dependency relation (e.g. `('aboya', 'nsubj')` = the wolf is the subject of "barked").

### Syntactic role classification
The script classifies each entity by its syntactic role:
- **Active agent** → `nsubj`, `ROOT`, `obl:agent` (entity performs the action)
- **Passive receiver** → `nsubj:pass` (entity undergoes the action passively)
- **Object** → `obj` (entity is the direct object of an action)
- **Noun complement** → `nmod` (entity qualifies a noun)
- **Other** → everything else

---

## WHAT I DID — STEP BY STEP

### Step 1 — Discovering the existing files

Exploring the GitLab repository, I found that the previous team had already:
- Extracted all animal/plant entities from the corpus
- Computed syntactic dependencies for each entity
- Created a referential-only file for animals (`dépendants_animaux_référentiels.csv`)

The script `analyse_dependances.py` already contained the agentivity classification logic. However, it had two problems that prevented it from running: a missing `seaborn` library and a Polars API incompatibility (the new version of Polars no longer allows UDFs without explicit return types).

### Step 2 — Fixing the analysis script

I rewrote the analysis as `analyse_agentivite.py`, processing rows one by one to avoid the Polars UDF issue. This produced the same results as the original script but without errors.

### Step 3 — Analysing referential animals

I ran the analysis on `dépendants_animaux_référentiels.csv` (106,410 rows, referential animals only — figurative cases already filtered by previous team).

**Results — referential animals (95,243 valid occurrences):**

| Category | N | % |
|---|---|---|
| Noun complement | 31,982 | 33.6% |
| **Active agent** | 23,265 | **24.4%** |
| Other | 20,040 | 21.0% |
| Object | 19,247 | 20.2% |
| Passive receiver | 709 | 0.7% |

**Verified examples:**
- Active agent: "Un loup **aboya** dans un vallon" (a wolf barked) ✅
- Active agent: "les loups nous **encerclaient**" (the wolves surrounded us) ✅
- Passive receiver: "Des chèvres **sont tenues** en laisse" (goats are kept on a leash) ✅
- Object: "en **chassant** un papillon" (chasing a butterfly) ✅
- Noun complement: "blessures de **loup**" (wolf wounds) ✅

All examples were manually verified as correctly classified.

### Step 4 — Analysing plants

I analysed `dépendants_PLANTES.csv` — all plant cases, referential AND figurative mixed together, because no referential filtering existed yet for plants.

**Results — plants (64,269 occurrences — referential + figurative mixed):**

| Category | N | % |
|---|---|---|
| **Noun complement** | 31,815 | **49.5%** |
| Other | 14,878 | 23.1% |
| Object | 9,727 | 15.1% |
| **Active agent** | 7,591 | **11.8%** |
| Passive receiver | 258 | 0.4% |

**Problem identified:** Checking examples manually, I found figurative cases contaminating the results:
- "La moutarde me **monte** au nez" → French idiom (getting angry), not a real plant
- "Schulmann m'a **tendu** une carotte" → French idiom (dangling a carrot), not a real plant
- "Le petit **pruneau** ne comprend pas" → "pruneau" = slang for a person, not a plant

These cases slightly distort the statistics. The previous team had done this filtering manually for animals (hence `dépendants_animaux_référentiels.csv` exists). **This filtering has not yet been done for plants.**

### Step 5 — Why not filter plants using Task 1 results right now?

**Option considered:** Use our literal/figurative classifier (Task 1) to classify all 63,599 plant mentions and 114,851 animal mentions in `ENTITES_TOTAL.csv`, then keep only referential cases and re-extract dependencies.

**Why it is not done yet:**

There are 63,594 unique (token, context) pairs for plants and 114,840 for animals. Our qwen3:30b model processes approximately 1 sentence every 2-3 seconds. This means:
- Plants: 63,594 × 2.5s ≈ **44 hours** of processing
- Animals: 114,851 × 2.5s ≈ **80 hours** of processing

This is not feasible before Wednesday's meeting.

**What our Task 1 results already give us:**

Our classifier achieves:
- Referential animals: **95.9%** precision ✅
- Referential plants: **100.0%** precision ✅

These numbers show our classifier is highly reliable on referential cases. When this filtering is eventually run (it will take several days of compute), the plant agentivity results will be much cleaner. Note: the plant results would only become *less* active after filtering (since figurative idioms like "tendre une carotte" count as agent uses), making the hierarchy even more pronounced.

### Step 6 — Building the human pipeline (new work)

The previous team had not analysed human characters at all. I built a new pipeline (`extract_humains.py`) using spaCy NER (`fr_core_news_lg`) to:
1. Detect all character names (PER entities) in each novel
2. Extract their syntactic role (Agent/Object/Passive/Complement)
3. Detect their gender (masculine/feminine) via morphology and contextual pronouns (il/elle, son/sa)
4. Filter out false positives (publisher names, author names, abbreviations)

**Runtime:** 45.5 minutes for all 925 novels  
**Output:** `dépendants_HUMAINS.csv` — 219,651 character mentions

**Results — humans (219,651 occurrences across 925 novels):**

| Category | N | % |
|---|---|---|
| **Active agent** | 81,755 | **37.2%** |
| Other | 62,395 | 28.4% |
| Noun complement | 44,184 | 20.1% |
| Object | 28,214 | 12.8% |
| Passive receiver | 3,103 | 1.4% |

**Gender breakdown:**
| Gender | N | % | Active agent % |
|---|---|---|---|
| Masculine | 118,142 | 53.8% | **38.2%** |
| Undetermined | 56,980 | 25.9% | — |
| Feminine | 44,529 | 20.3% | **37.7%** |

**Note on 25.9% undetermined gender:** This happens when:
- The name appears without nearby pronouns (il/elle) to resolve gender
- The name is ambiguous in French (Claude, Alex, Dominique)
- The name is foreign (English, Arabic, etc.) and spaCy does not know the gender
- It is a surname only, without contextual clues

This is not a bug — it reflects genuine uncertainty in the text.

**Verified examples:**
- Active agent: "Didier Schulmann me **rappelle** peu après" (Schulmann calls me back) ✅
- Passive receiver: "Alphonse aurait **été tué** par les tenanciers" (Alphonse was killed) ✅
- Object: "Il **s'appelle** Didier Schulmann" (His name is Schulmann) ✅

---

## FINAL RESULTS — AGENTIVITY HIERARCHY

| Category | Active agent | Passive receiver | Object | Noun complement | N total |
|---|---|---|---|---|---|
| **HUMANS (all)** | **37.2%** | 1.4% | 12.8% | 20.1% | 219,651 |
| Humans — masculine | 38.2% | 1.3% | 13.2% | 18.8% | 118,142 |
| Humans — feminine | 37.7% | 1.8% | 12.9% | 21.2% | 44,529 |
| **ANIMALS (referential)** | **24.4%** | 0.7% | 20.2% | 33.6% | 95,243 |
| **PLANTS (all, mixed)** | **11.8%** | 0.4% | 15.1% | 49.5% | 64,269 |

**Total analysed: 379,163 mentions across 925 novels**

### Conclusion

The hierarchy **Humans > Animals > Plants** is clearly confirmed:
- Humans act as active agents **37.2%** of the time
- Animals act as active agents **24.4%** of the time — **1.5× less than humans**
- Plants act as active agents only **11.8%** of the time — **3× less than humans**

Plants are used predominantly as **noun complements** (49.5%) — they describe things rather than do things. Animals fall between: more active than plants, but much less so than humans.

The male/female difference is minimal (38.2% vs 37.7%) — male and female characters have nearly identical agentivity in the corpus.

---

## KNOWN LIMITATIONS

1. **Plant results include figurative cases** — idioms like "tendre une carotte" or "les carottes sont cuites" are counted as plant mentions. This slightly inflates the agent% for plants. After referential filtering, plants would appear even less active.

2. **25.9% of human mentions have undetermined gender** — foreign names and ambiguous names cannot be reliably gendered from context alone.

3. **Human false positives** — spaCy NER occasionally picks up publisher names or author names from book headers. These are filtered by a blocklist but some may remain.

4. **Animal figurative cases** — the previous team's referential filter for animals was done manually. Our Task 1 classifier achieves 95.9% precision on referential animals, which is better. A re-filtered version could be produced with our classifier when compute time allows (~80 hours).

---

## WHAT REMAINS TO BE DONE

### High priority (before publication)

**[ALL ROWS BELOW: DONE — see the UPDATE sections further down for exact dates/numbers. Kept here only as the original historical plan.]**

| Task | Description | Estimated time |
|---|---|---|
| Plant referential filtering | Run Task 1 on 63,599 plant mentions → `dépendants_plantes_référentielles.csv` | ~44 hours compute |
| Animal re-filtering | Run Task 1 on 114,851 animal mentions → cleaner than previous team's manual filter | ~80 hours compute |
| Re-run dependency extraction | After filtering, re-run `get_token_dependencies.py` on referential-only cases | ~10 hours |
| Re-run agentivity analysis | Get final clean numbers for plants and animals | 1 hour |

### Low priority (future work)

- **Improve gender detection** — **DONE 2026-10-22, see UPDATE below (25.9% → 16.1% undetermined).** Originally: "the 25.9% undetermined could be reduced with a multilingual first-name database"
- **Separate referential/figurative for humans** — some "human" detections by spaCy may be personifications
- **Analysis by literary genre** — compare agentivity between ecological novels and mainstream fiction (filtering files already exist in the repo)
- **Loterre terms** — extend agentivity analysis to ecological/geographical terms (108,425 mentions in ENTITES_TOTAL)

---

## FILES PRODUCED IN THIS SESSION

| File | Description | Status |
|---|---|---|
| `morphosyntaxe/extract_humains.py` | Human character extraction pipeline using spaCy NER | ✅ Done |
| `morphosyntaxe/dépendants_HUMAINS.csv` | 219,651 human character mentions with role + gender | ✅ Done |
| `morphosyntaxe/analyse_agentivite.py` | Fixed analysis script (Polars-compatible) | ✅ Done |
| `morphosyntaxe/generate_report.py` | Report generation script | ✅ Done |
| `morphosyntaxe/resultats_agentivite_complet.txt` | Final comparative report with examples | ✅ Done |
| `morphosyntaxe/task3_full_report.md` | This document | ✅ Done |
| `dépendants_plantes_référentielles.csv` | Referential-only plants filtered by Task 1 | ✅ **Done — see UPDATE 2026-10-20 below** (final file is `dépendants_plantes_référentiels_REFRESH.csv`, this original filename was superseded) |
| `dépendants_animaux_référentiels_REFRESH.csv` | Referential-only animals filtered by Task 1 (our corrected version) | ✅ Done 2026-07-08, see update below |

---

## UPDATE — 2026-07-08 — Animal re-filtering completed (Known Limitation #4 resolved)

This closes out the "Animal re-filtering" item from **Known Limitations** and **What Remains To Be Done** above. Task 1 animaux finished on 2026-07-05 (including a Sunday retry pass, `retry_animaux_v2.py`, that fixed 3,665 previously-failed rows and patched the master label files in place — the corrected file is `resultats/task1_animaux_labels.csv` / `_full.csv`, **not** the `.bak_before_v2_patch` versions).

### Method

1. **Filtered** `resultats/task1_animaux_labels_full.csv` (127,945 rows, corrected Sunday labels) down to `task1_label == "référentiel"` → 89,681 rows.
2. **Joined** against `dépendants_ANIMAUX.csv` (the spaCy dependency-parse file `analyse_agentivite.py` consumes) on `(fichier, token_lexique, lemme, sentence)` to recover the `tête`/`dépendants`/`tête_de_tête` syntactic-role columns needed for classification.
3. **Bug found and fixed during step 2:** an initial join using Python's stdlib `csv` module mis-parsed `dépendants_ANIMAUX.csv` — it contains Python-tuple-repr strings (e.g. `('Caviar', 'ROOT')`) with embedded quote characters that break stdlib `csv`'s quoting rules, silently shifting fields on many rows and producing a bogus 89.6%-"Autre" result. Switched to `polars` (same library `analyse_agentivite.py` already uses successfully) — this fixed it.
4. **Coverage gap found:** `dépendants_ANIMAUX.csv` (built 2026-05-31, before Task 1 existed) turned out to be missing dependency-parse data for the entire "bestsellers" subset of the corpus (13,094 rows) plus 2,243 rows within corpus_principal — 15,337 rows never dependency-parsed at all. Initial join matched only 76,297/89,681 (85.1%) référentiel rows for this reason.
5. **Coverage gap closed:** re-ran dependency parsing on the missing 15,337 rows using `fr_core_news_lg` (the model actually installed in this environment, consistent with the sibling `extract_humains.py` script) with the same head/head-of-head logic as `scripts/get_token_dependencies.py` + `extract_humains.py`. Parsed 14,906/15,337 (97.2%) successfully; 431 tokens could not be relocated in the re-parse (comparable residual rate to the original file). Merged into `dépendants_ANIMAUX_COMPLET.csv` (127,681 rows). Re-ran the join: **86,082/89,681 matched (96.0% coverage)**.

### Final results — animals, référentiel-only, corrected Task 1 labels, full corpus coverage

| Category | N | % |
|---|---|---|
| Noun complement | 29,254 | 34.0% |
| **Active agent** | 20,472 | **23.8%** |
| Object | 18,549 | 21.5% |
| Other | 17,091 | 19.9% |
| Passive receiver | 716 | 0.8% |

Compared to the original (Joanna's manual filter, N=95,243): 24.4% active agent, 0.7% passive → now **23.8% active agent, 0.8% passive** on our own corrected classifier. Essentially unchanged — this is a confirmation, not a reversal. The hierarchy **Humans (37.2%) > Animals (23.8%) > Plants (11.8%)** holds.

Remaining 3,599 unmatched rows (4.0%) are residual (mostly the 431 re-parse misses plus minor sentence-formatting mismatches between corpus_principal/bestsellers source formats) — a small, reasonable gap compared to the original 15%.

### Files produced

| File | Description |
|---|---|
| `morphosyntaxe/dépendants_ANIMAUX_missing_rows.csv` | Newly dependency-parsed rows (bestsellers + corpus_principal gap), 14,906 rows |
| `morphosyntaxe/dépendants_ANIMAUX_COMPLET.csv` | Full merged dependency file, 127,681 rows |
| `morphosyntaxe/dépendants_animaux_référentiels_REFRESH.csv` | Final référentiel-only animal file for agentivity analysis, 86,082 rows |

**Task 3 animal side is now done.** Only the plant side remains, blocked on Task 1 plantes finishing (running now, ~50% as of 2026-07-08 midday).

## UPDATE — 2026-10-20 — Plant side completed (Task 3 agentivity now fully done)

Task 1 Plantes finished and was corrected well before this update (confirmed complete/audited as of early October). The same coverage-gap-closing work (steps 1-5 of the Method above) had already been done for plants at some point between the previous update and now, under the same file-naming convention, but was never carried through to a final analysis or written up — `analyse_agentivite.py` was still hardcoded to the old pre-refresh file list. This update is just that last step: pointing the analysis at the already-prepared plant file and running it.

**Verified the existing plant files are legitimate before trusting them**, rather than assuming the naming match was enough: `dépendants_PLANTES.csv` (64,270 rows) + `dépendants_PLANTES_missing_rows.csv` (7,517 rows) ≈ `dépendants_PLANTES_COMPLET.csv` (71,765 rows) — the same additive pattern as the animal side's missing-rows merge. The final `dépendants_plantes_référentiels_REFRESH.csv` (58,637 rows) covers 58,637/59,968 = **97.8%** of the corrected Task 1 Plantes référentiel rows (59,968, from `resultats/task1_plantes_labels_full.csv`) — comparable to (slightly better than) the animal side's 96.0%.

Re-ran `analyse_agentivite.py` against both REFRESH files together as a cross-check: the animal numbers reproduced exactly (23.8% / 0.8% / 21.5%), confirming the method and the plant file are both sound.

### Final results — plants, référentiel-only, corrected Task 1 labels, full corpus coverage

| Category | N | % |
|---|---|---|
| Noun complement | 29,809 | 50.8% |
| Other | 13,063 | 22.3% |
| Object | 9,038 | 15.4% |
| **Active agent** | 6,491 | **11.1%** |
| Passive receiver | 236 | 0.4% |

(Total: 58,637 référentiel-only mentions.)

Compared to the rough mixed figure reported above (11.8% active agent, figurative + referential combined on 64,269 rows): referential filtering brought it down to **11.1%**, exactly the direction the original report predicted ("after referential filtering, plants would appear even less active"). The hierarchy **Humans (37.2%) > Animals (23.8%) > Plants (11.1%)** holds, now on clean, fully-corrected, référentiel-only data for all three categories.

**Task 3's agentivity analysis is now fully complete for all three categories** (humans, animals, plants). Remaining Task 3 items are unrelated to this agentivity number: the multilingual name-detection extension (separate, in progress) — none of these change the result above.

## UPDATE — 2026-10-20 (same day) — humans bestsellers gap closed + passive-voice fix

Closed both remaining known Task 3 gaps immediately after the plant-side work above.

### Humans bestsellers coverage gap
`dépendants_HUMAINS.csv` only ever covered `CORPUS_TOTAL` (corpus_principal, 925 novels) — the 88-novel bestsellers subset (`CORPUS_Bestsellers/`) was never run through `extract_humains.py` at all, confirmed via direct set-difference against the real bestsellers novel list (not just a filename-pattern guess): 88/88 missing. Reused `process_novel()` from `extract_humains.py` directly (same `fr_core_news_lg` model, same head/head-of-head logic) via a new small script, `extract_humains_bestsellers_gap.py`, appending to the existing file rather than overwriting it. Added 28,309 rows across all 88 novels. `dépendants_HUMAINS.csv` now covers 1,013 unique novels (925 + 88 — exact, no duplicates).

### Passive-voice "être-auxiliary" fix
Quantified before fixing: pulled every `nsubj:pass` row for humans (3,231 total) and inspected the actual governing word. 914 of them (28.3%) were governed by a French verb that simply takes **être** as its normal auxiliary (mourir, aller, venir, rester, naître, devenir, sortir, arriver, partir, entrer, rentrer, monter, descendre, retourner, revenir, parvenir — the classic "verbes qui se conjuguent avec être" set) or a pure être+adjective predicate (content, assis, triste...) — structurally identical to a passive construction for spaCy's parser ([subject] + être + participle), but not semantically passive: nobody is acting on the subject. The original note's "likely **mostly** an artifact" overstated it — genuine passives (tué, arrêté, aimé, critiqué, accusé, blessé...) are still the majority, 71.7%.

Fixed in `analyse_agentivite.py`'s shared `classify_relation()` (used by all three categories, so the fix applies uniformly, not just to humans): an `nsubj:pass` row governed by one of these verbs/predicates is now reclassified as "Autre" rather than "Récepteur passif" — not forced into "Agent actif" either, since these sentences aren't the subject acting on someone else, just describing a state the subject underwent on their own.

### Final results — all three categories, full coverage, both fixes applied

| Category | Active agent | Passive | Object | Noun complement | Other | N |
|---|---|---|---|---|---|---|
| **Humans** | **37.8%** | 1.0% | 13.1% | 19.7% | 28.4% | 247,960 |
| **Animals** (référentiel) | 23.8% | 0.8% | 21.5% | 34.0% | 19.9% | 86,082 |
| **Plants** (référentiel) | 11.1% | 0.4% | 15.4% | 50.8% | 22.3% | 58,637 |

Humans' passive figure moved as expected once the être-auxiliary contamination was removed: **1.4% → 1.0%**. Animals and plants barely moved (0.8%→0.8%, 0.4%→0.4%) — the contamination was proportionally much smaller there, exactly as expected since human mentions have far more "died/left/arrived/became" constructions than animal/plant ones.

**Hierarchy holds, now on fully-corrected, full-coverage, both-known-gaps-closed data: Humans (37.8%) > Animals (23.8%) > Plants (11.1%).**

**Task 3's agentivity analysis is now genuinely complete** — no more known gaps on this specific number. The only remaining Task 3 item is the separate multilingual name-detection extension (full-corpus run in progress as of this update).

## UPDATE — 2026-10-20 (later same day) — multilingual names finished, filtered per Riccardo, and merged into the final humans number

The multilingual name-detection run finished the full 925-novel corpus (209,427 rows this run; 227,510 combined with the earlier 72-novel partial run — 219,651 `fr_model` + 7,859 `multilingual_model`).

Sent Riccardo the real full-corpus false-positive breakdown and got a ruling the same day. Full category breakdown, by unique name and by occurrence, with real examples pulled from the actual classification (`multilingual_name_classification_v2.csv`):

| Category | Unique names | % (unique) | Occurrences | % (occ.) | Decision | Examples |
|---|---|---|---|---|---|---|
| Plausible real name | 4,600 | 97.0% | 7,193 | 91.5% | **Kept** | Albert Camus, Amir Sadeghi, Zina... |
| Fictional/mythological | 42 | 0.9% | 74 | 0.9% | **Kept** | Barbie, Betty Boop, Bovary, Caliban, Don Quichotte, Dracula, D'Artagnan, Gargantua |
| Common noun/title confirmed | 28 | 0.6% | 417 | 5.3% | Removed | Ancêtre, Autre, Bureau, Camelot, Coran, Dieu, Fainéant |
| Fragment too short to judge | 35 | 0.7% | 90 | 1.1% | Removed | Al, An, CP, D., Do |
| Ambiguous (nickname-as-name) | 16 | 0.3% | 53 | 0.7% | Removed | Chérie, Cicatrice, Divine, Empereur, Faucheuse, Miroir |
| Brand/org/artwork | 18 | 0.4% | 27 | 0.3% | Removed | Armani, Chanel, Goldwyn Mayer, Mein Kampf, Metallica |
| Place name | 3 | 0.1% | 4 | 0.1% | Removed | Angleterre, Sotchi, Vichy |
| Tokenization artifact | 1 | 0.0% | 1 | 0.0% | Removed | "Ra-  chid Hchicha" (hyphenation split) |

**Riccardo's ruling** (verbatim): "I would count fictional characters inside the fictions as characters" (kept) — "you can eliminate the ambiguous, and the mistakenly flagged" (removed). Brand/place/fragment removal was my inference under the same "mistakenly flagged, eliminate" logic, not his explicit words — flagged back to him in case he wants any of those kept.

Filtered file: `morphosyntaxe/dépendants_HUMAINS_multilingual_FILTERED_RB20261020.csv` (7,267 kept multilingual-only rows, 592 removed). Raw unfiltered extraction kept separately for reference.

**Merged the filtered 7,267 rows into `dépendants_HUMAINS.csv`** (backup kept: `dépendants_HUMAINS.csv.bak_pre_multilingual_merge_20261020`) and re-ran `analyse_agentivite.py` for the true final number.

### Final results — humans, full French-only + filtered multilingual coverage

| Category | N | % |
|---|---|---|
| **Active agent** | 96,082 | **37.6%** |
| Other | 73,313 | 28.7% |
| Noun complement | 50,082 | 19.6% |
| Object | 33,191 | 13.0% |
| Passive receiver | 2,559 | 1.0% |

(Total: 255,227 mentions — 247,960 French-only + 7,267 filtered multilingual.)

Barely moved from the pre-merge figure (37.8%/1.0%/13.1% → 37.6%/1.0%/13.0%) — expected, since the multilingual additions are only ~2.8% of the total. **Hierarchy holds: Humans (37.6%) > Animals (23.8%) > Plants (11.1%).**

Also resolved the same day: Task 2's gold set 15 blank rows confirmed by Riccardo as false positives (not figurative), marked `x` — no code change needed, both scoring scripts already exclude non-valid-category values regardless of whether they're blank or `x`. Task 4.5's 45 blank `categorie_compare` rows reconciled: his stated rule (15 false positives + IMAG + COUL) accounts for 42; the remaining 3 are LOC_IDIOM rows (same "no compare-target" logic, he just didn't name that category) — except id=169 ("éléphants," tagged IMAG) unexpectedly has a compare-category filled in, flagged back to him as a genuine anomaly, not resolved yet.

**Task 3 is now fully complete, including the multilingual names extension, merged and reflected in the final numbers.** Open items outside Task 3's own scope: Riccardo's id=169 anomaly question, and whether he confirms the inferred brand/place/fragment removals.

## UPDATE — 2026-10-21 — all remaining items closed, plus the animal-form re-parse gap found and fixed

Riccardo's reply closed both outstanding items: id=169 ("the dogs have been disguised in elephants, so it is an image, but you have a comparé: indeed you can eliminate it, to make it simple") — blanked in the gold file to match the rest of IMAG; and the Loterre-term agentivity extension ("I would drop this, it is not necessary") — permanently out of scope.

Separately, a gap-audit (prompted by a research-documentation pass over the project's full July-October history) found that **the animal-forms lexicon fix from August never actually propagated into Task 3**, despite being on the known plan since 2026-10-05. Verified directly: zero of the 99 new derived animal word forms (chienne, louveteau, lionne, etc.) appeared anywhere in Task 3's dependency files, and the dependency files themselves predate the new-forms lexicon by about 2 hours on the same day — they could not possibly include it.

**Fixed 2026-10-21**: re-parsed the 4,287 new-form corpus rows with spaCy (`fr_core_news_lg`, now confirmed installed — the earlier "not available" blocker no longer applies), filtered to the 2,777 référentiel rows via the real Task 1 labels (1,510 were figuré, consistent with the already-known ~35% figurative skew for these forms), and merged into `dépendants_animaux_référentiels_REFRESH.csv` (86,082 → 88,859 total référentiel mentions).

**Final animal number, now including the complete lexicon**: 23.9% active agent / 0.8% passive / 21.5% object (barely moved from 23.8%/0.8%/21.5% — the gap was real, but its practical impact was small given the addition is only ~3% of the total). **Hierarchy unchanged: Humans (37.6%) > Animals (23.9%) > Plants (11.1%).**

**Task 3 now has zero open items of any kind** — this statement was true for the original scope (référentiel-only agentivity hierarchy, 3 categories) but is corrected below: it does not account for work done, or requested, after this date.

## UPDATE — 2026-10-22 — gender detection fix (done, but never previously recorded here)

The "25.9% undetermined gender" limitation named earlier in this report (see KNOWN LIMITATIONS and WHAT REMAINS TO BE DONE) was actually fixed the same week this report was last touched, but the fix was never written up until this entry (found during a 2026-10-30 audit, not by anyone flagging it at the time).

**The fix**: the original gender-detection method (spaCy morphology, falling back to nearby-pronoun counting) had a measured **18.0% error rate** against unambiguous first names, since proximity pronoun-counting doesn't actually resolve which character a nearby pronoun refers to. Replaced with `gender_guesser` (a real first-name gender database) as the PRIMARY source whenever a token's first word is a recognized first name — measured **0.0% error rate, 1.4% unknown** on the same validation sample. Falls back to the original morphology-based value only when `gender_guesser` doesn't recognize the name at all (e.g. "le narrateur", or names outside its database).

One real bug caught and fixed during this same pass: `gender_guesser`'s database false-matches common French function words as foreign-language names (e.g. "Mon"→female, "Son"→mostly_male, "Ma"/"Mais"/"Me"→male) — for a multi-word reference like "Ma mère," this was wrongly using the determiner's bogus match instead of the real noun. Fixed by filtering through spaCy's French stopword list before any `gender_guesser` lookup.

**Result**: undetermined-gender rate dropped from 25.9% to **16.1%** (83.9% of human mentions now have a determined gender) — a real, meaningful improvement, measured fresh on 2026-10-30 against the current `dépendants_HUMAINS.csv` (255,227 rows): masculin 55.4%, féminin 28.5%, indéterminé 16.1%.

Script: `morphosyntaxe/fix_gender_column.py`. Backup of the pre-fix file preserved at `dépendants_HUMAINS.csv.bak_pre_gender_fix_20261022`.

## UPDATE — 2026-10-30 — 2 real open items found AND closed the same day

A full audit (triggered by the user asking "is this task completely done?") found two genuine, Riccardo-requested extensions beyond the original scope that were started but never finished, and never flagged as open anywhere:

**1. Figurative-mention agentivity (Riccardo's request) — now complete.** The original agentivity hierarchy only ever covered référentiel mentions. Riccardo asked for the same analysis on figurative mentions. Step 1 (dependency-parsing, `morphosyntaxe/parse_figuratif_dependencies.py`) was already done (98.1% match rate). **Step 2 (running `analyse_agentivite.py`'s classification on this data) run 2026-10-30** — took under 8 seconds (pure spaCy-derived data, no GPU/LLM involved). Results saved to `resultats_agentivite_figuratifs.txt`:

| | Agent actif | Passif | Objet | N |
|---|---|---|---|---|
| Animaux figuratifs | 16.0% | 0.3% | 13.4% | 39,791 |
| Plantes figuratifs | 12.0% | 0.3% | 11.6% | 9,351 |

**New finding**: figurative animal mentions show notably *lower* agency (16.0%) than référentiel animal mentions (23.9%) — when animals are used metaphorically, they're less often the grammatical subject/actor. Plants show almost no difference (12.0% figuratif vs. 11.1% référentiel).

**2. Prix du roman d'écologie subcorpus breakout (Riccardo's request, email 2026-10-23/24) — now complete.** A separate count of Task 1 and Task 3 metrics for the 47-novel Prix du roman d'écologie subcorpus, run 2026-10-30, took 11 seconds. Results saved to `resultats_prix_ecologie_breakout.txt`:

- **Task 1 (référentiel/figuré)**: Prix-Écologie novels use animals far more literally than the corpus as a whole — 82.3% référentiel vs. 69.9% corpus-wide (17.7% figuré vs. 30.1%). Plants show a smaller version of the same pattern (90.2% vs. 86.5% référentiel).
- **Task 3 (agentivity)**: Prix-Écologie animals show *higher* agency than the corpus average (28.4% vs. 23.9% active agent), and plants too (13.3% vs. 11.1%). Both passive-voice rates are also slightly higher (animals 1.2% vs. 0.8%; plants 0.5% vs. 0.4%).
- **Reading**: ecology-prize-winning fiction appears to depict animals and plants more as real, acting presences in the world and less as rhetorical decoration, compared to the broader corpus — consistent with what you'd expect from novels specifically recognized for ecological engagement.

**Current status: Task 3 is now genuinely, completely done.** Original hierarchy complete, gender fix complete (documented above), figurative-mention agentivity complete, Prix-Écologie breakout complete. No known open items.

