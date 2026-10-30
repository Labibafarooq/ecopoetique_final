# Task 3 (Agentivity Analysis) — Complete Research History, Project Start → 2026-10-21

Sourced directly from: `MASTER_DOCUMENTATION.md`, `PROJECT_DOCUMENTATION.md`, `morphosyntaxe/task3_full_report.md` (all dated UPDATE sections), both full meeting transcripts (`riccardo_25june_meetingTranscript.md`, `métaphore/Riccardo_second_meeting.txt`), the live memory store's `MEMORY.md` index and relevant memory files, direct inspection of production scripts and data files, and direct reading of real log files for timing data. Where a period, detail, or duration could not be recovered from any of these sources, it is stated as unrecorded/unknown rather than guessed or estimated from unrelated figures.

## Research hypothesis (unchanged since the project's start)

> Are animals and plants more passive agents compared to humans in contemporary French novels?

Classifies every human/animal/plant mention by syntactic role via spaCy dependency parsing: **Active agent** (`nsubj`/`ROOT`/`obl:agent`), **Passive receiver** (`nsubj:pass`), **Object** (`obj`), **Noun complement** (`nmod`), **Other** (everything else). This task does not use qwen3 or any LLM — its bug class is dependency-parse coverage gaps and rule-mapping errors, not prompt/model calibration issues, which is why it has no gold set (see methodology section) and was workable throughout every GPU freeze that blocked Tasks 0/1/2/4.5.

---

## Chronological history, project start (2026-05-31) → 2026-10-21

### 2026-05-31 — the pre-existing dependency files are built (predates this project's own Task 3 work)

The previous research team (Johanna et al.) built the raw dependency-parse files this project would later inherit: `dépendants_ANIMAUX.csv` (126,201 rows, all occurrences, not yet filtered to référentiel-only) and `dépendants_PLANTES.csv` (68,920 rows, same). A third file, `dépendants_animaux_référentiels.csv` (106,410 rows), is the previous team's own référentiel-only filter, done manually. **No timing data survives for this original build** — it predates this project's own documentation and no log or dated note records how long it took or what method/model generated it, beyond that it used some form of dependency parsing matching spaCy's tag conventions.

### 2026-06-22 — original build of this project's own Task 3 pipeline

`PROJECT_DOCUMENTATION.md`'s dated report for this day: `analyse_dependances.py`, an earlier attempt at the agentivity classifier, had two blocking bugs — a missing `seaborn` import and a Polars UDF (user-defined function) API incompatibility — that prevented it from running at all. Rewritten the same day as `analyse_agentivite.py`, switching to a row-by-row processing approach specifically to avoid the Polars UDF issue, producing identical category logic without the crash. **Duration of this rewrite is not recorded.**

**Original référentiel-animals result** (95,243 occurrences, using the previous team's manually-filtered file): 24.4% active agent (23,265) / 0.7% passive (709) / 20.2% object (19,247) / 33.6% noun complement (31,982) / 21.0% other (20,040).

**Original plants result** (64,269 occurrences — mixed figurative+référentiel, since no référentiel-only filter existed yet for plants at this point): 11.8% active (7,591) / 0.4% passive (258) / 15.1% object (9,727) / 49.5% noun complement (31,815) / 23.1% other (14,878). Contamination found by manual example-reading: "la moutarde me monte au nez" (idiom, "to lose one's temper," not a real plant reference), "Schulmann m'a tendu une carotte" (idiom, "dangling a carrot"), "le petit pruneau ne comprend pas" ("pruneau" used as slang for a person, not a plum). Filtering was explicitly deferred at this point because Task 1 (the literal/figurative classifier needed to do the filtering) wasn't finished yet — **Task 1's own compute estimate at the time was ~44h for plants and ~80h for animals**, a real, recorded duration figure, though it belongs to Task 1's timeline, not Task 3's.

**Humans pipeline — entirely new work, not inherited.** The previous team never analyzed humans at all. Built `extract_humains.py` using spaCy NER (`fr_core_news_lg`) to detect character names (PER entities), extract syntactic role, detect gender via morphology plus contextual pronouns, and filter false positives (publisher/author names accidentally caught by NER). **Recorded runtime: 45.5 minutes for all 925 novels** — the one clean, explicit timing figure that survives from this original-build period, found directly in `task3_full_report.md`'s own text. Output: `dépendants_HUMAINS.csv`, 219,651 mentions.

**Humans result** (219,651 occurrences): 37.2% active agent (81,755) / 1.4% passive (3,103) / 12.8% object (28,214) / 20.1% noun complement (44,184) / 28.4% other (62,395). Gender breakdown: masculine 53.8% of mentions (38.2% active agent), feminine 20.3% (37.7% active agent), undetermined-gender 25.9% (no nearby pronoun, ambiguous names like Claude/Alex/Dominique, foreign names, surname-only references — flagged explicitly as reflecting genuine textual ambiguity, not a pipeline bug).

**Hierarchy, first established this day**: Humans (37.2%) > Animals (24.4%, roughly 1.5× less) > Plants (11.8%, roughly 3× less) as active agents.

### 2026-06-25 — first supervisor meeting, hierarchy approved

Full transcript: `riccardo_25june_meetingTranscript.md`. Riccardo reviewed the active/passive breakdown live. A specific worked example discussed directly in the transcript (not just paraphrased in later documentation): "Julien tua le lion" → lion is a direct Object; "le lion fut tué par Julien" → lion is Passive receiver (`nsubj:pass`); "le lion mangea Julien" → lion is Active agent (subject of an active verb); "Julien fut mangé par le lion" → lion is **still Active agent**, specifically via the oblique-agent relation (`obl:agent`) of the passive construction — the lion is doing the eating even though the sentence is grammatically passive. Riccardo, on being confused why the passive-agent category seemed low in number relative to active: this worked example resolved his confusion about the counting logic. He also asked, live, why the five categories' percentages don't sum to 100% — answered that "Other" is the implicit fifth bucket covering syntactic relations that don't fit the four named categories (prepositional phrases, appositions, existential constructions like "il y a des lions") — the project noted this needed to be documented explicitly going forward, which is why every table in this document always shows all five categories, not just the headline three.

The Humans > Animals > Plants hierarchy was approved at this meeting. Riccardo also requested, at this meeting, extending human-name detection beyond the French-only spaCy model to catch English/Arabic-origin names, explicitly flagging an overfitting risk in his own words ("a name called bar in any other language") and proposing mid-sentence capitalization as one possible validation signal. **No duration/timing data exists for the meeting's technical content itself** (meetings are discussions, not runs), but this is the direct origin point of the multilingual-names extension described below.

### ~early July 2026 — second supervisor meeting (exact date uncertain)

Full transcript: `métaphore/Riccardo_second_meeting.txt`. Exact date not pinned down in the transcript itself; content places it in early July, with Task 1 animaux mid-run at the time. Direct transcript quote, Riccardo looking at `dépendants_HUMAINS.csv` on screen: *"So you didn't have a gold set for this?"* / *"No, I made it myself because it didn't give me the gold set for humans and I just ran it."* (line ~529 of the transcript). This exchange was specifically about the human **names** check, not the active/passive/etc. role classification — both full transcripts were searched exhaustively for any mention of a role-classification gold set, and none exists anywhere, in either transcript or on the filesystem.

At this meeting, Riccardo also: asked to see example rows from the human-agentivity results and was *surprised the percentage of undetermined-gender names was so high* — the direct origin of the multilingual-names extension's urgency, not merely an abstract "French models miss foreign names" observation made in the void. Confirmed this was plausibly caused by the French-only spaCy model missing Arabic-origin and some English-origin names common in the corpus's many Francophone-Africa/Maghreb-set novels. Also raised, a second time, the overfitting-risk concern about multilingual name detection.

### Why there is no gold set for Task 3 (methodology, established at/after these two meetings)

This is a deliberate methodological choice, not a shortcut taken because a gold set was unavailable. Task 3's classification is **deterministic** — a fixed rule mapping spaCy's dependency-parse tags to categories, not a model making a probabilistic judgment call under uncertainty — so there is no calibration behavior to characterize statistically the way Tasks 1, 2, and 4.5 need a large gold set to validate an LLM's output against. The only two ways an error can enter this pipeline are (a) spaCy mis-parsing a sentence, or (b) the fixed rule mapping the wrong tag to the wrong category for some construction — both well-suited to a targeted manual spot-check of real sentences, not better served by a formal gold set. This was demonstrated in practice, not just argued theoretically: the 45-row spot-check described below (2026-07-10) caught a real, previously-missed bug that the original 2026-06-22 report's much shallower 3-example check had missed entirely.

### 2026-07-08 — animal-side coverage refresh (two real bugs found and fixed)

1. **Parsing bug**: `dépendants_ANIMAUX.csv` contains Python-tuple-repr strings with embedded quotes that break stdlib `csv`'s quoting rules, silently shifting fields — this produced a false 89.6% "Autre" result at one point before being caught. `analyse_agentivite.py` already used Polars for its own reads, which doesn't have this problem, so switching confirmed and fixed it. General lesson recorded going forward: any script reading `dépendants_*.csv` must use Polars, never stdlib `csv`.
2. **Coverage gap**: `dépendants_ANIMAUX.csv` (built 2026-05-31, before Task 1 even existed) never covered the bestsellers subset (13,094 rows) at all, and was short a further 2,243 rows even within corpus_principal. Closed by re-parsing 14,906 missing rows with `fr_core_news_lg`, reusing head/head-of-head dependency logic from `extract_humains.py`. **Duration of this specific re-parse is not explicitly recorded** in any source checked for this document — only the plants-side equivalent two days later has an explicit rows/sec figure (see below); this document does not assume the animal-side rate matched it, since the two runs are not confirmed to have used identical hardware/conditions.

Merged file: `dépendants_ANIMAUX_COMPLET.csv` (127,681 rows — 112,775 original + 14,906 new, confirmed to match exactly). Final référentiel animal numbers: 23.8% active agent / 0.8% passive / 21.5% object, 86,082 mentions, 96% coverage — barely moved from the pre-fix 24.4%/0.7%/20.2% (95,243), confirming the hierarchy wasn't an artifact of the coverage gap.

Also started this same day: the full 925-novel multilingual-name-detection run (see immediately below).

### 2026-07-08 — multilingual names extension: built, bug-fixed, tested, launched

Built `morphosyntaxe/extract_humains_multilingual.py`: runs `Davlan/xlm-roberta-base-ner-hrl` (CPU-only multilingual NER, confirmed zero GPU usage) alongside the French-only spaCy pass, keeping only new PER candidates the French model missed. Four real bugs found and fixed via direct output inspection — the project's established house rule being never to trust a "looks like it worked" run without checking actual extracted names:

1. **Subword-splitting**: XLM-R's tokenizer sometimes splits one name into two adjacent zero-gap PER spans ("Émile"→"É"+"mile", "Théodore"→"Th"+"éodore"). Fixed by merging consecutive zero-gap PER spans.
2. **One-sided truncation**: some names had only half tagged as PER at all ("Mauny"→only "ny" survived, "Lippmann"→only "pmann"). Fixed by extending any span to the nearest word boundary regardless of the model's own tagging.
3. **Animal/plant false positives**: 'Ours' (=bear) tagged as PERSON — a real risk given the corpus's whole subject matter. Fixed via cross-check against `lexiques/ANIMAUX.txt`/`PLANTES.txt` plus spaCy lemma + French gender-variant stripping (catches "Ourse"→"ours", "chatte"→"chat").
4. **Place-name false positives**: 'Sables' (Sables-d'Olonne) passed every other filter since it's a genuinely, consistently-capitalized proper noun. Fixed via cross-check against every LOC entity the French spaCy pass already tags in the same novel.

A 5th guard, `is_known_org` (checks against ORG entities like band names), was found already present in the code on a 2026-07-08 re-verification pass but had not previously been documented anywhere.

**5-novel test, re-verified 2026-07-08** (after an initial failed attempt with plain `python3` due to a missing spacy/transformers environment — resolved by using the correct `labelimg_env` Python environment instead): 897 total rows (811 fr_model + 86 multilingual_model), confirmed the fixes were stable, not a fluke. **No per-novel or total timing figure recorded for this specific 5-novel test.**

**Full 925-novel run launched 2026-07-08.** Per-novel rate established from the later completion data (see 2026-10-20 below): approximately 33 seconds per novel on average across the full run, though this blends two very different hardware/load periods (the original obtic-gpu1 box through July, the new DGX node from some point in the undocumented gap onward) so it should not be read as a single consistent rate. **ETA at launch time was stated as ~33h on CPU** (~130s/novel assumed at the time — a figure that turned out to be a significant overestimate per novel, see the final completion numbers below, though the overall real elapsed time ended up far longer than even that pessimistic estimate once the multi-month pause is counted). GPU was never tried for this extension at any point — a decision point that was simply never made, not a deliberate choice against it.

**2026-07-11**: the Riccardo-requested false-positive-rate estimate for the partial run was completed. At that point the run covered 72/925 novels (7.8%), 18,083 rows (16,676 fr_model + 1,407 multilingual_model). Methodology note of real significance: the *first* version of the estimation script used an automated heuristic (lowercase the name, re-run through spaCy, check the POS tag) — found unreliable on manual review, since it wrongly flagged genuine foreign/rare names (Abdelkader, Anissa, Azzouze, Ourida, Wafaa, Soraya) as "common nouns," precisely because spaCy's French model doesn't recognize unfamiliar names once decapitalized. That version was discarded in favor of hand-checking all ~533 unique names against real sentence context, across three correction passes. **No timing figure recorded for the hand-checking effort itself.**

**Results at 72/925 novels, by unique name (533 = 100%)**: plausible real name 78.0% (416), fictional/mythological 7.9% (42), common noun/title confirmed 5.3% (28), brand/org/artwork 3.4% (18), ambiguous/nickname 3.0% (16), fragment too short 1.7% (9), place name 0.6% (3), tokenization artifact 0.2% (1).

**By total occurrences (1,407 = 100%)**: plausible real name 73.2% (1,030), common noun/title 15.4% (217) — dominated by "Dieu" alone at 177 occurrences (12.6% of all multilingual-only occurrences, sample-verified to always mean "God"), fictional/mythological 4.2% (59), fragment 2.8% (40), ambiguous 2.5% (35), brand/org 1.5% (21), place 0.3% (4), tokenization 0.1% (1).

Note sent to Riccardo at the time, explicitly leaving the acceptability call to him: is a ~22-27% false-positive rate on the multilingual-only additions acceptable given the model still nets 416+ plausible real names many existing extraction would have missed, or does the common-noun/fictional-character contamination (especially "Dieu") need a filtering pass first?

### 2026-07-10 — plants-side coverage refresh, with the one clean rate figure that survives from this period

Same class of coverage-gap bug as animals: `dépendants_PLANTES.csv` (May 31, pre-Task-1) missing the entire bestsellers subset (0/87 files) plus 2,756 corpus_principal rows — confirmed directly from `reparse_plantes_missing.py`'s own header comment, which explicitly names "bestsellers subset + a gap in corpus_principal" as its two targets. `fr_core_news_lg` had vanished from the environment (packages don't persist between sessions on this project's infrastructure at the time) and was reinstalled — **reinstall duration not recorded**. Re-parsed 7,516 missing rows **at ~60 rows/sec on CPU — meaning roughly 125 seconds (~2.1 minutes) of actual processing time**, 99.7% match rate. Merged file `dépendants_PLANTES_COMPLET.csv` (71,764 rows). Final référentiel coverage: 97.8% (up from 87.3%), file `dépendants_plantes_référentiels_REFRESH.csv` (58,637 rows) — though the *analysis* of this file (the actual 11.1%/0.4%/15.4% numbers) was not run until 2026-10-20, over three months later (see below) — a genuine, three-month gap between data being ready and the corresponding number actually being produced.

Two new issues diagnosed the same day, neither fixed yet at the time:
1. **Humans bestsellers coverage gap**: `extract_humains.py`'s `CORPUS_DIR` only ever pointed at `CORPUS_TOTAL`, confirmed 0/88 bestsellers novels present in `dépendants_HUMAINS.csv`. The headline 37.2% human active-agent figure was, from this point on, explicitly flagged as unverified against ~9% of the corpus.
2. **Passive-voice être-auxiliary contamination**: a 45-row manual spot-check (3 per category × 5 categories × 3 populations — chosen specifically because this deterministic task has no gold set to score against) found animaux and plantes fully clean (15/15 each) but humans showing all 3/3 sampled "Récepteur passif" rows (Jésus/blond, Charles/assis, Dan/gêné) were actually être+adjective predicates, not real passives. A systematic check of all 3,103 human passive-tagged rows found the dominant governing words were être-auxiliary intransitive verbs (morte, assis, restée, venue/venu, rentré, allée/allé, revenue, entrée, né, devenue — state/movement verbs, not passives). Diagnosed as "likely most of the 1.4% figure" at the time, not yet quantified precisely, not yet fixed. **No timing figure recorded for the spot-check itself** (45 rows read manually — a human-effort task, not a compute run, so wall-clock duration was never the relevant measure here). A second, smaller issue noted in the same spot-check: spaCy mis-tagging subject-verb inversion after reported speech ("dit-il") as an object rather than a subject — flagged as minor dialogue-pattern contamination of the Object bucket, never chased further.

### 2026-07-10 through 2026-07-22 — GPU freeze; multilingual run paused at 72/925 (7.8%), not resumed

The multilingual names run was explicitly paused, not progressed, through this stretch — this is a real, deliberate pause, not silent abandonment; GPU access for the project's other tasks (0/1/2/4.5) was frozen project-wide, and while the multilingual extension itself was CPU-only and could technically have continued, it was not restarted during this window. The 533 unique names from the partial run were reviewed again for concrete false-positive examples (common nouns: Tordu, Mauvais, Cicatrice, Dieu; fictional characters: Tintin, Yoda, Don Quichotte; brand/org: Chanel, Tsahal, Libé; tokenization artifacts from hyphenation breaks).

### 2026-07-22 → 2026-10-05 — undocumented gap (confirmed, not filled in)

No memory record or dated documentation entry exists for this roughly 2.5-month span. The live memory store's own index explicitly states it "fills the memory gap between the 2026-07-10 GPU freeze and today [2026-10-05]" and that "nothing was recorded in that ~3-month window before this session." Whatever happened to Task 3 specifically in this window — if anything — is not recoverable from any source checked for this document. The project did migrate servers (old `obtic-gpu1` single-A40 box → new 8×A100-40GB DGX node) somewhere in this window, confirmed only by the new machine's existence, not by a dated migration record — meaning the exact date the hardware underlying all later timing figures changed is itself unknown.

### 2026-08-20 → 2026-10-07 — adjacent, non-Task-3 work with a deferred Task-3 implication

Not Task 3 itself, but worth noting as context: Riccardo's 2026-08-20 email flagged a lexicon gap (feminine/young-animal word forms missing from `ANIMAUX.txt`, e.g. chienne/louveteau). This work — lexicon edits, homograph disambiguation for chatte/rate/mule/ourse/laie/chenille, extraction — was entirely CPU-only and entirely about Task 1's lexicon, but its own documentation explicitly scoped a "Task 3 re-parse" as a dependent future step, blocked on `fr_core_news_lg` being reinstalled. As of the latest record checked before this document's own audit (the 2026-10-08 cross-task audit, below), this Task-3-re-parse step for the new animal forms was still queued, not started. **This gap is resolved later in this same document — see 2026-10-21 (same day, later), below** — it turned out to have genuinely never been done, and was found and fixed as a direct result of writing this document.

### 2026-10-08 — cross-task audit confirms the state frozen since July

A full status audit on this date confirms, independently, that nothing had moved since the July diagnoses: humans bestsellers gap still open, passive-voice contamination "confirmed real, never fixed," multilingual names still at 72/925 (7.8%), paused. Also newly noted: the "fictional characters counted as human" question had been "flagged internally as worth asking, never actually sent to Riccardo" — the first record of that specific question existing at all.

### 2026-10-20 — all three remaining agentivity gaps closed in one session

**Plant-side refresh completion.** The coverage-gap-closing files (`dépendants_PLANTES_COMPLET.csv`, `dépendants_PLANTES_missing_rows.csv`) were found to already exist from the 2026-07-10 work above, matching the animal-side fix's naming pattern — but this was *verified*, not trusted on filename alone: row-count math was checked first (`dépendants_PLANTES.csv` 64,270 + `missing_rows.csv` 7,517 ≈ `COMPLET.csv` 71,765, the same additive pattern as animals), then the final référentiel file (58,637 rows) was cross-checked against the corrected Task 1 plantes labels (59,968 référentiel rows) for 97.8% coverage before being trusted. Only the final analysis step had actually been missing — the data had been sitting ready since July. **Running `analyse_agentivite.py` itself on already-prepared Polars-backed files is a fast operation (seconds, not minutes) — no specific duration recorded, but not a bottleneck by nature of the tool.** Result: **plants 11.1% active agent / 0.4% passive / 15.4% object** (58,637 mentions) — down from the old mixed 11.8%, in exactly the direction the original 2026-06-22 report predicted once figurative contamination was removed. Animal numbers reproduced exactly as a cross-check (23.8%/0.8%/21.5%), confirming both the method and the plant file were sound.

**Humans bestsellers coverage gap, closed.** Confirmed via a real set-difference against the actual 88-novel bestsellers list (not a filename-pattern guess — bestsellers filenames don't contain the word "bestseller" at all). 88/88 novels confirmed missing. New script `extract_humains_bestsellers_gap.py` reused `process_novel()` from `extract_humains.py` directly, against `CORPUS_Bestsellers/`, adding 28,309 rows. **Timing**: the run log (`extract_humains_bestsellers_gap.log`) shows per-novel row counts and an "ETA=0min" marker at completion, but does not print an explicit total-elapsed-time summary the way later same-day runs do — the log file's own timestamp is 2026-10-20 11:44:40, but without a logged start time this document cannot state a precise duration; given the comparable 925-novel human extraction took 45.5 minutes, an 88-novel subset using the identical per-novel method would be expected to take on the order of a few minutes, but this is an inference from a comparable run, not a recorded fact, and is stated as such rather than presented as a measured figure. File now covers exactly 1,013 unique novels (925+88).

**Passive-voice été-auxiliary contamination, fixed and re-quantified.** The old July note said "likely mostly" an artifact. Quantified precisely before touching anything: of all 3,231 human `nsubj:pass` rows, **914 (28.3%)** were être-auxiliary intransitive verbs or être+adjective predicates — not genuine passives. Genuine passives are still the majority, **71.7%**. Fix: an exclusion set (`_ETRE_AUX_OR_ADJ_PREDICATES`) added to the shared `classify_relation()` function in `analyse_agentivite.py`, reclassifying matching rows to "Autre." **No separate timing recorded for this step** — it is a code change plus a Polars re-aggregation over already-loaded data, inherently fast (seconds), not a long-running process worth logging a duration for.

**Final numbers after both fixes, full coverage**: Humans 37.8% active / 1.0% passive / 13.1% object (247,960 mentions). Hierarchy confirmed: Humans > Animals > Plants.

**Multilingual names, full corpus completed, filtered, and merged — same day, later.** The run resumed from the 72-novel partial point and processed the remaining 853 novels. **Exact, directly-logged completion time: "Done in 471.1 minutes"** (≈7.85 hours of CPU time for the 853-novel resumed portion — found directly in `extract_humains_multilingual_FULL_run3.log`, the clearest single timing figure in this entire document's research). Combined totals: 227,510 rows (219,651 fr_model + 7,859 multilingual_model). The real false-positive breakdown on the complete corpus (91.5% plausible by occurrence) was sent to Riccardo, replacing the partial-run 73.2% estimate.

**Riccardo's filtering ruling, same day**: keep plausible real names + fictional/mythological characters ("I would count fictional characters inside the fictions as characters" — this also directly answers the "fictional characters as human?" question first raised 2026-10-08); eliminate ambiguous nickname-cases and mistakenly-flagged common nouns. He did not explicitly name brand/org/artwork, place names, or too-short-to-judge fragments; these were eliminated under the same logic as an inference, flagged explicitly as such.

Filtered: 7,267 of 7,859 multilingual-only mentions kept (592 removed: 417 common-noun, 90 fragment, 53 ambiguous, 27 brand, 4 place, 1 tokenization). Merged into `dépendants_HUMAINS.csv`. Final humans number: **37.6% active agent / 1.0% passive / 13.0% object**, N=255,227. **Hierarchy: Humans (37.6%) > Animals (23.8%) > Plants (11.1%).**

### 2026-10-21 — final closure of all remaining open items

Two items closed via Riccardo's email replies to a 2026-10-20 status update:
1. **The Loterre-term agentivity extension** (a proposal, never committed to by either party, to extend the same analysis to ~108,425 climate-change/Anthropocene-vocabulary mentions) — Riccardo: "I would drop this, it is not necessary." Permanently out of scope.
2. A Task 4.5 gold-set anomaly (id=169, "éléphants") — resolved and the gold file corrected.

### 2026-10-21 (same day, later) — the animal-forms re-parse gap, found and closed, with exact timing

Prompted directly by this research-documentation pass: verified by reading the actual files that the August lexicon-gap work's "Task 3 re-parse" step — queued since 2026-10-05, never confirmed done anywhere — had in fact **never happened**. Direct proof: zero of the 99 new derived animal forms (chienne, louveteau, lionne, ourse, etc.) appeared as extracted tokens anywhere in Task 3's dependency files; and those dependency files are timestamped roughly two hours *before* the new-forms lexicon file was even created on 2026-10-05, so they could not possibly contain it regardless of content.

**Fixed the same day, with exact timing recorded this time.** `fr_core_news_lg` is now confirmed installed — the earlier blocker no longer applies. Built `reparse_animaux_newforms.py` by adapting `reparse_plantes_missing.py`'s proven template. Pulled 4,287 new-form rows from the production corpus files, re-parsed them — **recorded completion: 4,121/4,287 matched (96.1%) in 0.8 minutes of CPU time**, a direct, logged figure from this session's own run, confirming spaCy dependency parsing at this scale runs at roughly 5,300+ rows/minute on this hardware, consistent with the earlier plants-side 60 rows/sec (~3,600 rows/minute) figure from July, allowing for hardware differences between the old box and the new DGX node. Filtered to référentiel-only via the real Task 1 labels (1,510 figuré excluded, 35.2% of the 4,287), merged the resulting 2,777 référentiel rows into `dépendants_animaux_référentiels_REFRESH.csv` (86,082 → 88,859 total référentiel mentions).

**New, final animal number**: 23.9% active agent / 0.8% passive / 21.5% object. **Hierarchy, final and fully lexicon-complete: Humans (37.6%) > Animals (23.9%) > Plants (11.1%).**

This closes what had been the single most significant unresolved item in Task 3's entire history — a real gap that sat undiscovered for 11 days (2026-10-05 queued → 2026-10-21 found and fixed) purely because nothing had ever gone back to check whether a queued step actually ran.

---

## Timing summary table — every duration recovered from a real source in this document

| Date | What | Duration | Source |
|---|---|---|---|
| 2026-06-22 | `extract_humains.py`, full 925-novel run | **45.5 minutes** (CPU) | `task3_full_report.md`, stated directly |
| 2026-07-08 | Animal coverage-gap re-parse, 14,906 rows | not recorded | — |
| 2026-07-08 | Multilingual 5-novel verification test | not recorded | — |
| 2026-07-10 | Plants coverage-gap re-parse, 7,516 rows | **~60 rows/sec ≈ 2.1 minutes** (CPU) | `task3_full_report.md` / `MASTER_DOCUMENTATION.md`, stated directly |
| 2026-10-20 | Humans bestsellers gap fix, 28,309 rows (88 novels) | not explicitly recorded (inferred as "a few minutes" by comparison to the 45.5min/925-novel rate, not a measured figure) | log lacks a total-duration summary line |
| 2026-10-20 | Multilingual names, resumed 853-novel run | **471.1 minutes (≈7.85 hours)**, CPU | `extract_humains_multilingual_FULL_run3.log`, exact logged figure |
| 2026-10-21 | Animal new-forms re-parse, 4,287 rows | **0.8 minutes**, CPU | this session's own direct log output |

Everything else in Task 3's history that involved code changes, re-aggregation over already-parsed Polars data, or manual spot-checks is inherently fast (seconds for the code/data operations) or is a human-effort task where wall-clock duration was never the relevant measure (reading 45 sample sentences, hand-checking 533 names) — these are noted in the narrative above as "no timing recorded" rather than assigned a fabricated number.

---

## Part 2 — Gap audit: does the documentation actually match the code and data?

This section verifies specific claims by reading the real files directly, rather than trusting any prior write-up.

### Verified correct

- **The merge arithmetic is exactly right.** Directly counted: pre-merge `dépendants_HUMAINS.csv` = 247,960 rows; the filtered multilingual file has exactly 7,267 rows with `source=multilingual_model`; current `dépendants_HUMAINS.csv` = 255,227 rows. 247,960 + 7,267 = 255,227, exact.
- **`analyse_agentivite.py`'s actual code matches its own documentation exactly.** The `_ETRE_AUX_OR_ADJ_PREDICATES` exclusion set, read directly from the script, matches what memory describes, and the `files` list points at exactly the three expected REFRESH/merged files with current, accurate labels.
- **The plant-side bestsellers coverage question, raised as something to check, turns out to be a non-issue.** `reparse_plantes_missing.py`'s own header comment explicitly names "bestsellers subset + a gap in corpus_principal" as its two targets — already covered from July.

### Real gaps found (all resolved during this document's own writing)

1. ~~`morphosyntaxe/task3_full_report.md` is one day stale.~~ **Fixed 2026-10-21.** Now has a final UPDATE section covering the id=169 resolution, the Loterre-extension drop, and the animal-forms re-parse fix.
2. ~~The new-animal-forms Task-3-re-parse step has no confirmed resolution anywhere.~~ **Resolved 2026-10-21**, directly as a result of this audit flagging it. The citable animal figure is now 23.9%/0.8%/21.5% (supersedes 23.8%/0.8%/21.5%).
3. **Both master documentation files are stale relative to the last two days of work.** Neither `MASTER_DOCUMENTATION.md` nor `PROJECT_DOCUMENTATION.md` reflects the 2026-10-20/21 closures — they still describe the July-era open-items list as current.
4. **No formal accuracy figure has ever been computed for the multilingual name-detection pipeline itself** (as opposed to the false-positive-rate estimate, a precision-style estimate, not a recall/F1-style figure against any ground truth). Flagged as a known gap back in July, never closed.

No other category-vocabulary mismatches or silent exclusions were found in the agentivity classifier itself — `classify_relation()`'s five-way mapping is simple and consistent enough across all three populations' files that there is no equivalent of Task 0's `NAR_VAR` gap hiding here.

---

## Part 3 — 2026-10-22: Riccardo's two follow-up requests (gender-split, figurative-use agentivity)

Task 3 had been marked fully closed as of 2026-10-21 ("zero open items"). Riccardo's reply to the biodiversity-indices email reopened it with two new, concrete asks: (1) a gender split (male vs. female characters) of the existing agentivity numbers, and (2) testing agentivity on figurative mentions, not just référentiel ones. Both were genuinely new work — neither had ever been attempted.

### Core numbers re-verified unchanged before touching anything

Re-ran `analyse_agentivite.py` fresh: humans 37.6%/1.0%/13.0%, animals 23.9%/0.8%/21.5%, plants 11.1%/0.4%/15.4% — identical to every figure already on record. Confirmed none of tonight's work on either request touched the agentivity-role columns (`tête`/`tête_de_tête`) used to compute these.

### Gender-split agentivity — a real bug found and fixed mid-task

`dépendants_HUMAINS.csv` already had a `genre` column (masculin/féminin/indéterminé), populated by `extract_humains.py`'s `detect_gender()` — spaCy morphology first, falling back to counting il/elle-type pronouns in a ±10-token window around the name when morphology is empty (which it almost always is for proper names). **Measured its real accuracy before trusting it**: checked against 18,902 rows with unambiguous French first names (Monique, Antoine, Catherine, etc.) — **18.0% error rate** (3,394 mismatches), e.g. "Monique Lange" tagged masculin. Root cause: the pronoun-proximity fallback doesn't resolve which character a nearby pronoun actually refers to, so it just counts whichever gendered pronoun happens to be more frequent nearby — unreliable in any scene with multiple characters.

**Fix, first attempt**: installed `gender_guesser` (a real first-name gender database, pip-installed this session), verified it against the same 18,902-row sample — **0.0% error rate**, 1.4% unrecognized. Applied as the primary source (first word of `token_lexique` looked up directly), falling back to the original value only when unrecognized. Changed 48,044 of 255,227 rows.

**Bug found via this document's own re-audit discipline, not by accident**: spot-checked a random sample of 20 changed rows before trusting the fix. Found "Ma mère" (unambiguously feminine — "my mother") had been changed from the already-correct `féminin` to `indéterminé`. Traced the cause: `gender_guesser`'s database false-matches common French function words as names from other languages — confirmed directly: "Mon" (French "my") → `female`, "Son" (his/her) → `mostly_male`, "Ma"/"Mais"/"Me" → `andy`/`male`/`andy`. For a multi-word reference like "Ma mère" or "Mon père", the fix was reading the *determiner* as if it were the name, overriding an already-correct value derived from the real noun's morphology. Scope-checked the damage: "Ma" alone (1,170 occurrences), "Me" (528), "Mais" (507) — over 2,200 rows affected just from these three words, out of the 48,044 changed.

**Proper fix**: restored `dépendants_HUMAINS.csv` from the pre-fix backup, added a pre-filter using spaCy's own French stopword list (`spacy.lang.fr.stop_words`, 507 entries — confirmed it covers all three problem words) before any `gender_guesser` lookup, and reran. Result: 45,130 rows changed this time (vs. the buggy 48,044 — confirming ~2,900 false-positive matches correctly excluded). Re-validated: **1.15% error rate** on the same 18,902-row sample (holds steady, since none of those unambiguous test names were stopwords to begin with), "Ma mère" confirmed restored to `féminin`, and the top 200 most-frequently-matched tokens post-fix manually scanned for any remaining function-word contamination — none found (all genuine short/unusual names: Max, Ali, Ben, Tom, Léo, Zoé, etc.).

**Final gender distribution**: masculin 141,372, féminin 72,693, indéterminé 41,162 (of 255,227 total).

**Gender-split agentivity result** (computed via `classify_relation()` applied separately to each gender subset — same unmodified classification logic used throughout Task 3):

| | Men (141,372) | Women (72,693) |
|---|---|---|
| Active agent | 38.1% | **40.4%** |
| Passive receiver | 1.0% | 1.2% |
| Object | 13.3% | 13.2% |
| Noun complement | 18.9% | 18.9% |
| Other | 28.7% | 26.3% |

Women show a real, if modest, higher active-agent rate than men (40.4% vs. 38.1%, a 2.3-point gap) — notably the opposite direction from a naive stereotype-based prediction.

### Figurative-use agentivity — genuinely new, never attempted before tonight

Confirmed before starting that no figurative dependency-parse data had ever existed for Task 3 — only référentiel files (`dépendants_animaux_référentiels_REFRESH.csv`, `dépendants_plantes_référentiels_REFRESH.csv`) were ever built, consistent with Task 3's agentivity work having only ever covered literal mentions. Reconsidered Riccardo's literal wording ("test the agentivity also for the figurative use") against the project's actual structure: this project's figurative/référentiel distinction (Task 1's output) only applies to animal/plant mentions, not human ones, so this is about animal/plant figurative mentions specifically, not a human-side request.

**Scope**: pulled directly from Task 1's full label files — 39,791 figuré animal rows (of 132,332 total animal Task 1 rows) + 9,351 figuré plant rows (of 69,319 total) = 49,142 rows needing a fresh dependency parse.

**Method**: adapted the exact head/head-of-head extraction logic already used for the animal-forms re-parse (`reparse_animaux_newforms.py`, itself matching `scripts/get_token_dependencies.py`/`extract_humains.py`'s approach, model `fr_core_news_lg`) into a new script (`parse_figuratif_dependencies.py`) covering both populations in one pass, writing to two separate output files to match the existing référentiel-file convention. Tested on a 17-row sample first (100% match) before committing to the full run.

**Timing, directly measured**: 49,142 rows in **8.6 minutes**, CPU-only (no GPU involved, consistent with the rest of Task 3). 48,210/49,142 matched (98.1%) — the standard, expected match-rate shortfall from tokenization edge cases, same order of magnitude as every other dependency-parse run in this project.

**Result**:

| | Animals — figuré (39,791) | Animals — référentiel (88,859) | Plants — figuré (9,351) | Plants — référentiel (58,637) |
|---|---|---|---|---|
| Active agent | **16.0%** | 23.9% | **12.0%** | 11.1% |
| Passive receiver | 0.3% | 0.8% | 0.3% | 0.4% |
| Object | 13.4% | 21.5% | 11.6% | 15.4% |
| Noun complement | 34.1% | 33.7% | 37.2% | 50.8% |
| Other | 36.2% | 20.1% | 39.0% | 22.3% |

Animals show a real, meaningful drop in active-agent rate when used figuratively versus literally (16.0% vs. 23.9%) — when an animal word stands in for something else metaphorically, it is less likely to be the grammatical agent driving the sentence's action. Plants show no comparable shift (12.0% vs. 11.1%, essentially flat).

### Status as of 2026-10-22

Both of Riccardo's new requests are now complete: gender-split agentivity (bug found, fixed, verified, computed) and figurative-use agentivity (built from scratch, parsed, computed). Re-verified a third time at the user's explicit request before writing this section — core numbers, gender distribution, and figurative file row counts all reproduce exactly. Task 3 has no further known open items as of this writing.

### On research literature specifically (checked directly, not assumed)

Searched `MASTER_DOCUMENTATION.md`'s full Task 3 section, every `morphosyntaxe/*.py` script, and every memory file touching Task 3 for any citation of academic papers, published literature, or external research — found **none**. This is a real, accurate finding, not an omission: unlike Task 0 (which explicitly cites Conceptual Metaphor Theory / sequential chain-of-thought literature) or Task 2 (whose prompt-engineering choices were informed by comparable published techniques), Task 3's method is a simple, deterministic mapping from spaCy's own dependency-parse tags to five role categories — not a technique that itself needed literature grounding to justify. Its validity was established via manual spot-checks and cross-population consistency checks, not by appeal to external research.
