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

## STATUS: ALL 4 DELIVERABLES FULLY COMPLETE

| Deliverable | Status | Verified |
|---|---|---|
| Pielou's evenness | ✅ Done | Columns present in all 3 corpus files, both rarefaction sizes (20, 50), broken out by animaux/plantes/champignons/loterre/taxons |
| SAD | ✅ Done | Log-series beats log-normal on all 3 corpora on AIC/BIC (e.g. DigEco: AIC 28,588 vs. 29,327) — confirmed by direct inspection, not taken on trust |
| Beta diversity | ✅ Done, including per-category split | Confirmed via direct file read: both output files already contain the full breakdown — global, animaux, plantes, **champignons**, loterre, **taxons** — as separate categories |
| Hill numbers | ✅ Done | Per-book, per-corpus, per-year; cross-checked against SAD's own species count (exact match: 3,893 species for DigEco) |

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
