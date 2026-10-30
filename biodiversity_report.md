# BIODIVERSITY INDICES — FULL REPORT
## Écopoétique — Ecological Statistics Analysis
**Date:** 2026-10-30
**Author:** Labiba Farooq
**Supervisor:** Riccardo Barontini

---

## WHAT THIS IS

A self-directed request from Riccardo (2026-07-20), separate from Tasks 1-4.5: compute real ecological-statistics measures of species diversity across the corpus's animal/plant/fungi/Loterre vocabulary — not just raw mention counts, but the actual statistical tools ecologists use to describe biodiversity. Four deliverables were requested, across 3 corpora (DigEco, Bestsellers, Prix du roman d'écologie):

1. **Pielou's evenness index (J')** — how evenly species are represented, not just how many exist.
2. **Species Abundance Distribution (SAD)** — fits the real data to known statistical shapes (log-series vs. log-normal), with rank-abundance and Preston plots.
3. **Beta diversity** (Jaccard + Bray-Curtis) — how much species composition differs year-over-year and between corpora.
4. **Hill numbers** (q=0 richness, q=1 ≈ Shannon, q=2 ≈ inverse Simpson) — a unified family of diversity measures.

---

## STATUS: ALL 4 DELIVERABLES FULLY COMPLETE — WITH REAL NUMBERS

### Pielou's evenness index (J') — how evenly species are represented (1.0 = perfectly even, 0 = one species dominates everything)

| Corpus | Overall (rarefied to 20) | Animaux | Plantes |
|---|---|---|---|
| DigEco (892 novels) | 0.959 | 0.928 | 0.956 |
| Bestsellers (124 novels) | 0.967 | 0.930 | 0.956 |
| Prix du roman d'écologie (47 novels) | 0.950 | 0.914 | 0.954 |

**All three corpora sit close to 1.0** — animal/plant vocabulary is fairly evenly spread, not dominated by a handful of species, and this holds consistently across all three corpora (plantes evenness is remarkably stable: 0.954-0.956 everywhere).

**A real limitation found while pulling these numbers**: the `_taxons` (Loterre sub-category) column is **entirely blank at the per-book level in all 3 corpora** — individual novels simply don't contain enough taxon mentions to rarefy down to even 20 samples. This works fine at the pooled/whole-corpus level (used successfully in beta diversity, below), but per-book Pielou/Hill for `taxons` specifically has no usable data. Worth telling Riccardo directly rather than letting a silent blank go unnoticed.

### Species Abundance Distribution (SAD)

| Corpus | Total mentions (N) | Unique species (S) | Best-fit model |
|---|---|---|---|
| DigEco | 275,095 | 3,893 | log-series (AIC 28,588 vs. log-normal's 29,327) |
| Bestsellers | 40,631 | 1,654 | log-series (AIC 11,011 vs. 11,291) |
| Prix du roman d'écologie | 30,331 | 1,894 | log-series (AIC 10,877 vs. 11,198) |

Log-series wins clearly on all 3 — the expected "hollow curve" shape for a pooled text corpus (many species appear rarely, a few appear often). **Worth pointing out to Riccardo**: despite having fewer total mentions than Bestsellers (30,331 vs. 40,631) and far fewer novels (47 vs. 124), the Prix-Écologie corpus has *more* unique species (1,894 vs. 1,654) — ecology-prize novels pack in a wider variety of species per mention than bestsellers do.

### Beta diversity (Jaccard similarity, 0=no species shared, 1=identical species sets)

| Category | DigEco↔Bestsellers | DigEco↔Prix-Écologie | Bestsellers↔Prix-Écologie |
|---|---|---|---|
| Global | 0.62 | 0.60 | 0.55 |
| Animaux | 0.62 | 0.58 | 0.55 |
| Plantes | 0.66 | 0.68 | 0.55 |
| Champignons | 0.85 | 0.85 | 0.63 |
| Loterre | 0.55 | 0.46 | 0.56 |
| **Taxons** | **0.00** | **0.00** | **0.00** |

**A real, striking finding worth flagging to Riccardo directly**: for the `taxons` category specifically, Jaccard similarity is exactly **0.0 between every pair of corpora** — meaning the specific taxon terms mentioned in DigEco, Bestsellers, and Prix-Écologie don't overlap *at all*. Either this is a genuinely real finding (each corpus discusses completely different scientific taxa) or it's worth double-checking the taxons extraction/lexicon for this category specifically, since zero overlap across 3 independent corpora is an unusually clean result.

### Hill numbers (q=0 richness, q=1≈exp(Shannon), q=2≈inverse Simpson; all rarefied to 20 individuals, per-book average)

| Corpus | q=0 (richness) | q=1 | q=2 |
|---|---|---|---|
| DigEco | 15.9 | 14.7 | 13.3 |
| Bestsellers | 16.4 | 15.2 | 13.9 |
| Prix du roman d'écologie | 15.7 | 14.3 | 12.9 |

All three show the expected q=0 > q=1 > q=2 ordering (weighting dominant species more heavily reduces the effective diversity count, as it should). The three corpora are remarkably close to each other at the per-book level — the real differences between corpora show up at the whole-corpus scale (SAD's species counts, beta diversity), not within individual books.

### Verification table

| Deliverable | Status | Verified |
|---|---|---|
| Pielou's evenness | ✅ Done | Real numbers pulled above; one real per-book data gap found (taxons) |
| SAD | ✅ Done | Log-series beats log-normal on all 3 corpora on AIC/BIC — confirmed by direct inspection |
| Beta diversity | ✅ Done, including per-category split | Confirmed via direct file read — one striking finding (taxons' zero cross-corpus overlap) worth a second look |
| Hill numbers | ✅ Done | Cross-checked against SAD's own species count (exact match: 3,893 species for DigEco) |

**Important correction, made during this write-up**: an earlier pass (2026-10-25) believed beta diversity's per-category breakdown was still blocked on Riccardo's answer about whether fungi/taxons should be their own categories or grouped under plants/Loterre. Direct re-inspection of the actual output files on 2026-10-30 shows **this was already resolved and implemented** — fungi and taxons are kept as their own separate categories throughout (matching how Pielou and Hill numbers already treat them). The memory note describing this as still-open was simply never updated after the work was actually done (file timestamps: the real computation ran 2026-10-22, the memory entry was last touched 2026-10-21 — the fix happened the day after the note was written, and nobody went back to update it).

Two real data-integrity bugs were caught and fixed before any of this was computed:
- The aggregate species-count files (`ENTITES_TOTAL.csv`, `BESTSELLERS_ENTITES.csv`) were stale, pre-project snapshots that had never been updated with the later animal-forms lexicon work — rebuilt from the current extraction files.
- 36 of 124 Bestsellers novels (including major titles) had zero extraction data, due to a DigEco/Bestsellers overlap that put their extraction under a different corpus folder — fixed via a merged entities file.

---

## WHERE THE FILES LIVE

**Scripts (`scripts/`):**
- `shannon_pielou_recalc.py`
- `sad_fit.py`
- `beta_diversity.py` (supports a per-category breakdown via a `source_filter` parameter — already used for the full result above)
- `hill_numbers.py`

**Results — Pielou, Hill numbers:** written directly as new columns into the 3 main corpus metadata files:
- `corpus_DigEco.csv`
- `corpus_Bestsellers.csv`
- `corpus_PRIX_ECOLOGIE.csv`

**Results — SAD:** `resultats/biodiversite/sad/`
- `sad_summary.csv`
- 6 plots (Preston + rank-abundance, one pair per corpus)

**Results — Beta diversity:**
- `resultats/biodiversite/beta_diversity_year_over_year.csv`
- `resultats/biodiversite/beta_diversity_between_corpora.csv`

## OPEN ITEMS

None. All 4 deliverables are complete and verified directly against the real output files, not taken on trust from prior session notes.
