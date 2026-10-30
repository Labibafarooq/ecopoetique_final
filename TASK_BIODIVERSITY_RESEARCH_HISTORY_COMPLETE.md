# Biodiversity Indices — Complete Research History, 2026-07-20 → 2026-10-22

Sourced directly from the live memory store's `project_email_biodiversity_and_animal_forms.md` (the authoritative record of the original email ask and the parallel animal-forms lexicon thread), this session's own transcript (all implementation work from 2026-10-21 onward), and direct inspection of the production scripts (`scripts/shannon_pielou_recalc.py`, `scripts/hill_numbers.py`, `scripts/beta_diversity.py`, `scripts/sad_fit.py`) and their output files (`corpus_DigEco.csv`, `corpus_Bestsellers.csv`, `corpus_PRIX_ECOLOGIE.csv`, and everything in `resultats/biodiversite/`). Where a duration or detail could not be recovered from any of these sources, that gap is stated explicitly rather than filled in with a plausible-sounding guess, matching this project's standing documentation convention (see `TASK0_RESEARCH_HISTORY_COMPLETE.md` and `TASK3_RESEARCH_HISTORY_COMPLETE.md` for the same discipline applied to the other tasks).

## What this task is

Écopoétique studies how animals, plants, and biodiversity are represented across a 925-novel French corpus (Sorbonne Université / UPPA, supervised by Riccardo Barontini, worked on by intern Labiba Farooq). A previous team member, Joanna, had already computed a Shannon diversity index (species richness combined with evenness of abundance, using rarefied sampling to correct for differing text lengths) for the corpus's metadata files. On 2026-07-20, Riccardo asked for four additional biodiversity indices to be added on top of that existing Shannon work: Pielou's evenness index, a Species Abundance Distribution (SAD) analysis, beta diversity, and (marked optional) Hill numbers. This document covers that request end to end, including a parallel thread that turned out to be a real prerequisite for trusting any of it.

---

## 2026-07-20 — the original request

Riccardo's email (9:44 AM), sent via three GitLab metadata-file links (`corpus_Bestsellers.csv`, `corpus_DigEco.csv`, `corpus_PRIX_ECOLOGIE.csv`), asked for:

1. **Pielou's evenness index (J')** — derived from Shannon. He noted Joanna had already computed rarefied Shannon at two sample sizes (20 and 50) but was unsure which was more appropriate, and explicitly asked for Labiba's advice. Needed for the complete dataset and separately per taxonomic category (he named three: animals, plants, Loterre concepts). He also flagged the statistical requirement explicitly: if Shannon was computed by rarefaction, Pielou must be computed from the *same* rarefied Shannon values and the richness observed in the *same* rarefied sample, not two separate measurements.
2. **Species Abundance Distribution (SAD)** — construct the empirical SAD per corpus, fit both log-series and log-normal models, compare fits via AIC/BIC, produce rank-abundance and Preston plots. Notably, unlike items 1 and 3, this paragraph never asked for a taxonomic-category breakdown — only "for each corpus (and, if needed, for other groups of books)."
3. **Beta diversity** — Jaccard (presence/absence) and Bray-Curtis (abundance-weighted) dissimilarity, calculated for each year from 2001 onwards using 2001 as the baseline community, separately for animals/plants/Loterre/complete dataset, and also between the three main corpora as wholes.
4. **(Optional) Hill numbers** — q=0 (richness), q=1 (exponential of Shannon, "effective number of common species"), q=2 (inverse Simpson, "effective number of dominant species"), for the complete dataset and per category, using the same abundance data as Shannon/Pielou, and if possible at three scales: per individual book, per corpus, and per yearly subset.

Riccardo explicitly said September-or-later was fine (he had paternity leave coming up). Labiba's decision at the time, consistent with how this work was already informally tracked as self-directed and optional: defer it. Nothing was done on this request for roughly three months.

## 2026-08-20 → 2026-10-07 — a parallel thread that became a real prerequisite

Not part of the biodiversity request itself, but it directly affected whether any biodiversity number could later be trusted. On 2026-08-20, Riccardo separately flagged a lexicon gap: the existing animal lexicon only ever connected singular/plural forms of the same lemma, never feminine forms (chienne, ourse, lionne) or young-animal forms (louveteau) — 99 unique derived word forms across roughly 70 animal lemmas, confirmed by direct read of his attached spreadsheet. This work — lexicon edits, homograph disambiguation for six risky words (chatte, rate, mule, ourse, laie, chenille), and extraction — ran through September and into early October, entirely CPU-only. Riccardo's own email noted "we'll probably need to recalculate Shannon" once this was integrated. By 2026-10-07, extraction was done for 96 of the 99 forms plus confirmed `rate` disambiguation rows (3,914 rows merged into production); `chatte` was staged but not merged; `chenille` was deliberately held out pending Riccardo's own manual review. The full resolution of this thread (including the 2026-09-19 multi-parent-form decision and the eventual animal-forms re-parse) is documented in Task 3's own research history and this memory file; it is summarized here only because its consequence — stale species-count files — is what the biodiversity work had to catch before computing anything.

## 2026-10-21 — resumption, and two real data-integrity gaps found before computing anything

Picked back up on 2026-10-21, roughly 10 days before the end of Labiba's internship, on the assessment that Task 0, Task 2, and Task 3 had each reached stable stopping points that session. Before running any calculation, the underlying species-count data was checked against the actual corpus rather than trusted on file-naming alone — consistent with this project's standing rule (see `feedback_verify_homograph_risk_with_real_samples.md`) of verifying against real files, not summaries or memory. Two real, previously undiagnosed gaps were found this way:

1. **`resultats/corpus_principal/ENTITES_TOTAL.csv` and `resultats/bestsellers/BESTSELLERS_ENTITES.csv` — the aggregate species-count files Shannon and every new index actually read from — were frozen, pre-project snapshots.** Neither had ever been updated with the August-September animal-forms lexicon work described above, despite that work having been merged into the current production `ENTITES_contexte_animaux.csv` files months earlier. Confirmed directly: the frozen `ENTITES_TOTAL.csv` showed 114,851 animal rows — exactly matching the pre-project, Johanna-era baseline figure cited elsewhere in this project's documentation — while the current `ENTITES_contexte_animaux.csv` had 118,911. Rebuilt `ENTITES_TOTAL.csv`'s animal portion from the current extraction file (verified by independent cross-check: 3,963 new-form rows now present, an exact match to Task 3's own, separately-computed count of new-form rows reaching corpus_principal).
2. **36 of 124 Bestsellers novels had zero extraction data at all** in `BESTSELLERS_ENTITES.csv` — including major titles (*Limonov*, *Houris*, *Petit pays*). This is a different gap from the one Task 3 closed for `dépendants_HUMAINS.csv` (agentivity); this one is about the raw species-entity extraction itself. Root cause, confirmed by direct file lookup: those 36 novels are *also* DigEco novels (a 37-novel overlap between the DigEco and Bestsellers corpus lists), and their species data existed only under `corpus_principal`'s extraction, never under Bestsellers' own. Fixed by building `resultats/bestsellers/BESTSELLERS_ENTITES_MERGED.csv`, combining Bestsellers' own 88-novel extraction with the 36 missing novels' data pulled from `corpus_principal`. Verified: 124/124 novel coverage confirmed by direct set-intersection against `corpus_Bestsellers.csv`'s own novel list, not assumed from row counts.

No duration is recorded for either fix specifically — both were CSV-manipulation operations (filtering, merging, re-saving) on data already loaded, not long-running computations, and this document does not assign a fabricated timing figure to them.

## 2026-10-21 — the rarefaction-size question, answered with real data

Riccardo's standing question (20 vs. 50) was resolved empirically rather than by general reasoning. First, which of the two existing frozen Shannon columns corresponded to which size was not actually labeled in the data — `Shannon_rarefied_20` was explicitly named, but the plain `Shannon_rarefied` column's size was unstated. This was confirmed, not assumed: the exact Monte Carlo rarefaction procedure was reproduced directly against one novel's real token data (`Rodier-Jean_En-remontant-les-ruisseaux.txt`) at both candidate sizes, and the size=50 reproduction (3.42–3.52 across five independent seeds) matched the frozen `Shannon_rarefied` value (3.5067) far more closely than the size=20 reproduction (2.77–2.80) did — confirming the unlabeled column was size=50.

With both sizes correctly identified, the actual recommendation was made by checking real exclusion rates (texts too short to even reach the rarefaction threshold get dropped entirely) rather than by abstract preference:

| Corpus | Excluded at size=20 | Excluded at size=50 |
|---|---|---|
| DigEco (892 novels) | 3 (0.3%) | 35 (3.9%) |
| Bestsellers (124 novels) | not previously computed | 36 (29.0%) |
| PRIX_ECOLOGIE (47 novels) | not previously computed | 0 (0%) |

Size=50 was found to exclude nearly a third of the Bestsellers corpus — a real, substantial cost, not a minor tradeoff. The recommendation sent to Riccardo was size=20, with both sizes computed and retained regardless so nothing already-requested was lost.

## 2026-10-21/22 — Pielou implemented, and the email sent

`scripts/shannon_pielou_recalc.py` recalculates Shannon from scratch (not reusing the old frozen values) using Monte Carlo rarefaction (30 trials per novel, `random.sample` at a fixed size), computing richness (S) and Shannon entropy (H) from the *identical* sample in the *identical* trial loop — satisfying Riccardo's explicit methodological requirement, verified directly in the code rather than merely claimed. Pielou's evenness is then J' = H / ln(S). Run across both rarefaction sizes (20 and 50) for all three corpora, writing results directly into `corpus_DigEco.csv`, `corpus_Bestsellers.csv`, and `corpus_PRIX_ECOLOGIE.csv` as `Pielou_{20,50}[_category]` columns. An email was sent to Riccardo reporting Pielou as done, giving the data-backed rarefaction-size recommendation above, and asking one open question: whether fungi (champignons) should be grouped under "plants" and taxons under "Loterre concepts" (matching the pre-existing column-naming convention already present in the corpus's metadata before this session touched anything), or kept as separate categories in their own right. The email also flagged the two data-integrity gaps found and fixed above, in case they affected any Shannon numbers Riccardo had already looked at independently.

## 2026-10-21 — SAD implemented, and a re-reading correction

`scripts/sad_fit.py` constructs the empirical species-abundance distribution per corpus (pooling all novels' species counts within a corpus), fits Fisher's log-series via maximum likelihood (solving S/N = -(1-x)ln(1-x)/x for x by root-finding, then alpha = N(1-x)/x), fits a two-parameter log-normal via `scipy.stats.lognorm`, compares both via AIC (2k − 2logL) and BIC (k·ln(n) − 2logL), and produces rank-abundance and Preston plots. Run and verified for all three corpora at the complete-dataset level. Results, read directly from `resultats/biodiversite/sad/sad_summary.csv`:

| Corpus | N (mentions) | S (species) | Best model (AIC) |
|---|---|---|---|
| DigEco | 275,095 | 3,893 | log-series |
| Bestsellers | 40,631 | 1,654 | log-series |
| PRIX_ECOLOGIE | 30,331 | 1,894 | log-series |

Log-series won by AIC in all three corpora — consistent with a "hollow curve" abundance pattern (a small number of very frequent species, a long tail of rare ones), which is the expected shape for pooled text-corpus species mentions and matches what the rank-abundance plots show visually (a steep initial drop followed by a long flat tail at abundance 1-2). SAD was initially treated, and communicated to the user, as blocked on the same fungi/taxons categorization question as Pielou and beta diversity. A direct re-reading of Riccardo's original email text found this was incorrect: unlike the Pielou and beta-diversity paragraphs, the SAD paragraph never asked for a taxonomic-category breakdown at all, only a per-corpus one. SAD was therefore already fully complete at this point and had never actually been blocked on anything.

## 2026-10-21 — beta diversity, first pass, deliberately left incomplete

`scripts/beta_diversity.py` computes Jaccard and Bray-Curtis dissimilarity (1) year-over-year within a corpus against a baseline year, and (2) between the three corpora as pooled wholes. A first pass was run at the complete-dataset level only (no taxonomic-category split), covering year-over-year for DigEco and Bestsellers (both have novels from 2001) and between-corpora comparisons for all three. The per-category breakdown was explicitly not attempted at this point, even though the script's `source_filter` parameter already supported it — this was a deliberate, named decision not to proceed on an unconfirmed assumption about how Riccardo wanted fungi and taxons grouped, made the same way the categorization question itself was left open rather than guessed at.

## 2026-10-21 — Hill numbers implemented in full, including per-category

`scripts/hill_numbers.py` computes q=0 (species richness, the count of distinct species), q=1 (exp of Shannon entropy, "effective number of common species"), and q=2 (inverse Simpson, 1/Σp², "effective number of dominant species"). Unlike Pielou and beta diversity, Hill numbers were implemented immediately with a full per-category breakdown, using the same provisional three-category grouping (animals / plants+fungi / Loterre+taxons) that the Pielou email had flagged as an open question — a deliberate choice, made because Hill numbers were explicitly marked optional by Riccardo, so proceeding on a provisional assumption carried less risk than it would have for a required deliverable.

A real methodological judgment call was made and documented at this point: per-book Hill numbers use the same rarefied Monte Carlo sampling as Shannon and Pielou (necessary, since book lengths vary enormously and rarefaction is exactly what corrects for that), but corpus-level and year-level Hill numbers are computed directly from the full, unrarefied pooled abundance data. The reasoning: rarefying an already-large pooled sample (thousands of mentions) down to 20 or 50 individuals would discard nearly all the information in the sample rather than correct a length-comparability problem, since the bias that rarefaction exists to fix (short books being unfairly summarized) does not apply to a pooled corpus- or year-level aggregate in the same way.

Cross-check performed at this point: the corpus-level global richness computed independently by `hill_numbers.py` for DigEco (3,893 species) matched the species count computed independently by `sad_fit.py` for the same corpus exactly — confirming the two scripts' pooling logic agreed with each other without having been written to share code for that specific calculation.

## 2026-10-22 — Riccardo's reply, and the categorization correction

Riccardo's reply (10:28 AM) to the Pielou email: *"I would put taxons and fungi in separate categories."* This differed from the provisional three-category grouping used for Pielou and Hill numbers — he wanted five categories (animals, plants, fungi, Loterre concepts, taxons), not three.

Both `scripts/shannon_pielou_recalc.py` and `scripts/hill_numbers.py` were updated to the corrected five-way `CATEGORIES` dictionary. Before rerunning, the session's own incorrect three-category columns were removed from `corpus_DigEco.csv`, `corpus_Bestsellers.csv`, and `corpus_PRIX_ECOLOGIE.csv` — precisely scoped to only the columns this session had added (identifiable by containing an explicit rarefaction size, `_20_` or `_50_`, combined with `plantes` or `loterre_taxons`), leaving the original pre-existing `Shannon_rarefied_plantes` and `biodiv_index_plantes` columns (Joanna-era work, predating this session entirely) untouched. Both scripts were rerun across both rarefaction sizes for all three corpora. Verification directly against the resulting files: zero old-scheme columns remained, 20 new category-specific columns were present per file (`{Shannon_rarefied,Pielou}_{20,50}_{animaux,plantes,champignons,loterre,taxons}` plus the Hill-number equivalents), and Pielou values remained within the mathematically valid [0,1] range across all categories.

## 2026-10-22 — beta diversity completed at the per-category level

With the categorization question now definitively answered, `scripts/beta_diversity.py` was rewritten to the same five-category `CATEGORIES` dictionary and rerun. Verified directly: 288 year-over-year rows (24 years × 2 corpora × 6 categories including "global", exact expected count) and 18 between-corpora rows (3 corpus pairs × 6 categories, exact expected count) were produced. A self-vs-self sanity check (comparing the 2001 baseline year against itself, which must equal exactly 0.000 dissimilarity under both Jaccard and Bray-Curtis by construction) was run across every row and passed with zero exceptions.

One real, interesting finding surfaced at this point, read directly from `resultats/biodiversite/beta_diversity_between_corpora.csv`: taxons showed Jaccard = 0.000 between every single pair of corpora (DigEco vs. Bestsellers, DigEco vs. PRIX_ECOLOGIE, Bestsellers vs. PRIX_ECOLOGIE) — meaning zero taxon species are shared in common between any two corpora. Cross-checked against the underlying counts in `resultats/biodiversite/hill_numbers_corpus_year.csv`: each corpus has only 1-2 distinct taxon species in its 2001 (or 2017, for PRIX_ECOLOGIE) baseline community. This is almost certainly a sparsity artifact of how few taxon-category mentions exist in the corpus at all, not a genuine ecological signal about taxonomic composition — flagged as such rather than presented as a finding of substance.

## 2026-10-22 — the PRIX_ECOLOGIE year-baseline extension

Riccardo's original specification said "from 2001 onwards, using 2001 as baseline." PRIX_ECOLOGIE's own novel list, checked directly against `corpus_PRIX_ECOLOGIE.csv`, has no entries before 2017 — a 2001 baseline simply does not exist for this corpus, through no implementation choice. Rather than leave PRIX_ECOLOGIE out of the year-over-year analysis entirely, `beta_diversity.py`'s `year_over_year()` function — which already auto-detects "the earliest available year in the given metadata file" as its baseline, rather than hardcoding 2001 — was called for PRIX_ECOLOGIE as well, using its own natural earliest year (2017) as the baseline instead. This was done without first asking Riccardo: judged to be a strictly additive extension that stays within the clear intent of the original request (tracking compositional change over time, per corpus) rather than a deviation needing permission. Verified directly: 48 new rows (8 years, 2017–2024, × 6 categories, exact expected count), self-vs-self sanity check passed with zero exceptions across all 336 total year-over-year rows (288 + 48) once combined with the DigEco/Bestsellers rows from the prior step.

## 2026-10-22 — full final audit pass

Before considering the task complete, a full re-audit was performed: both of Riccardo's emails were re-read word-for-word against what had actually been delivered (this is what caught the SAD re-reading correction documented above); the source entity files were re-verified as still current (118,911 animal rows, matching the live extraction file exactly; 124/124 Bestsellers coverage, confirmed again); and every formula was re-verified directly against its standard mathematical definition by reading the actual code, not by trusting an earlier description of it:

- Pielou: J' = H / ln(S)
- Hill numbers: q0 = species count; q1 = exp(Shannon H); q2 = 1/Σp² (inverse Simpson)
- Jaccard dissimilarity: 1 − |A∩B| / |A∪B|
- Bray-Curtis dissimilarity: Σ|xᵢ−yᵢ| / Σ(xᵢ+yᵢ)
- Fisher's log-series MLE: S/N = −(1−x)ln(1−x)/x solved for x by root-finding; α = N(1−x)/x
- Log-normal: two-parameter fit via `scipy.stats.lognorm`, location fixed at 0
- AIC = 2k − 2·logL; BIC = k·ln(n) − 2·logL

The "global" (complete-dataset) category was also re-confirmed, directly in the code of all three scripts, to genuinely include all five sub-source types unfiltered (the filtering condition is skipped entirely when the category's source set is `None`), not accidentally excluding anything.

One real, worth-flagging limitation was identified and retained in the final state, not silently fixed or hidden: PRIX_ECOLOGIE's between-corpora comparisons and its own (2017-baselined) year-over-year trend are both present and valid, but its year-over-year series cannot be directly compared to DigEco's or Bestsellers's year-over-year series on the same year axis before 2017, since no PRIX_ECOLOGIE data exists for those earlier years. This is a genuine property of the underlying corpus, not an implementation gap.

---

## Final state of all four deliverables, as of 2026-10-22

| Deliverable | Status | Script | Output |
|---|---|---|---|
| Pielou's evenness index | Complete — complete dataset + 5 categories, both rarefaction sizes, all 3 corpora | `scripts/shannon_pielou_recalc.py` | `corpus_{DigEco,Bestsellers,PRIX_ECOLOGIE}.csv`, `Pielou_{20,50}[_category]` columns |
| Species Abundance Distribution | Complete — per corpus (never required a category split) | `scripts/sad_fit.py` | `resultats/biodiversite/sad/sad_summary.csv` + 6 plots |
| Beta diversity | Complete — complete dataset + 5 categories, year-over-year (DigEco/Bestsellers from 2001, PRIX_ECOLOGIE from its own 2017 baseline) and between all 3 corpora | `scripts/beta_diversity.py` | `resultats/biodiversite/beta_diversity_year_over_year.csv` (336 rows), `beta_diversity_between_corpora.csv` (18 rows) |
| Hill numbers (optional) | Complete — complete dataset + 5 categories, per book/corpus/year | `scripts/hill_numbers.py` | `corpus_{DigEco,Bestsellers,PRIX_ECOLOGIE}.csv`, `Hill_q{0,1,2}_{20,50}[_category]` columns + `resultats/biodiversite/hill_numbers_corpus_year.csv` |

## Open items

None, as of 2026-10-22. All four parts of Riccardo's original 2026-07-20 request are complete, correctly categorized per his 2026-10-22 reply, and verified against the underlying source files and formula definitions directly rather than assumed correct. A follow-up email was drafted reporting the completed work (including the formulas used, the two data-folders used — `CORPUS_TOTAL`, covering DigEco and PRIX_ECOLOGIE, and `CORPUS_Bestsellers` — and the two data-integrity gaps found and fixed) and flagging the PRIX_ECOLOGIE year-range limitation; whether this depends on any further reply from Riccardo is not yet known as of this document's writing.
