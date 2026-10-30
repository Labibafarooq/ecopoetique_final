"""
Prix du roman d'écologie subcorpus breakout — requested by Riccardo
(email, 2026-10-23/24, item 1): a SEPARATE count, not pooled into the main
corpus totals, for Task 1 (référentiel/figuré) and Task 3 (agentivité)
metrics specifically for the 47-novel Prix du roman d'écologie subcorpus.

Confirmed before building this: zero filename overlap between
corpus_PRIX_ECOLOGIE.csv and the other corpus files (corpus_DigEco.csv,
corpus_Bestsellers.csv), and all 47 Prix novels already have entity data in
resultats/corpus_principal/ENTITES_TOTAL.csv and the Task1/Task3 result
files below (produced by the main-corpus runs, since these novels are part
of corpus_principal's underlying text set) — no new extraction needed,
just filtering + separate aggregation.

Reuses classify_relation from analyse_agentivite.py directly rather than
re-describing the agentivity classification logic.
"""
import sys, os, csv
import polars as pl
sys.path.insert(0, os.path.dirname(__file__))
from analyse_agentivite import classify_relation

BASE = os.path.expanduser("~/ecopoetique")

PRIX_FILE = f"{BASE}/corpus_PRIX_ECOLOGIE.csv"
TASK1_ANIMAUX = f"{BASE}/resultats/task1_animaux_labels_full.csv"
TASK1_PLANTES = f"{BASE}/resultats/task1_plantes_labels_full.csv"
TASK3_ANIMAUX = f"{BASE}/morphosyntaxe/dépendants_animaux_référentiels_REFRESH.csv"
TASK3_PLANTES = f"{BASE}/morphosyntaxe/dépendants_plantes_référentiels_REFRESH.csv"


def load_prix_novels():
    with open(PRIX_FILE, encoding="utf-8") as f:
        return set(r["File"] for r in csv.DictReader(f, delimiter="\t") if r.get("File"))


def task1_breakout(path, label, prix_novels):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    prix_rows = [r for r in rows if r["fichier"] in prix_novels]
    total_all = len(rows)
    total_prix = len(prix_rows)
    from collections import Counter
    counts_all = Counter(r["task1_label"] for r in rows)
    counts_prix = Counter(r["task1_label"] for r in prix_rows)
    print(f"\n{'='*60}\n  TASK 1 — {label} — Prix du roman d'écologie (47 novels)\n{'='*60}")
    print(f"  Total mentions (all corpus): {total_all:,}")
    print(f"  Total mentions (Prix subcorpus only): {total_prix:,}  ({total_prix/total_all*100:.1f}% of corpus total)")
    for cat in ("référentiel", "figuré"):
        n_all = counts_all.get(cat, 0)
        n_prix = counts_prix.get(cat, 0)
        pct_all = n_all / total_all * 100 if total_all else 0
        pct_prix = n_prix / total_prix * 100 if total_prix else 0
        print(f"  {cat:<14} all-corpus: {n_all:>7,} ({pct_all:5.1f}%)   Prix-only: {n_prix:>6,} ({pct_prix:5.1f}%)")
    return total_prix, counts_prix


def task3_breakout(path, label, prix_novels):
    # NOTE: classify_relation() wraps both literal_eval calls in one
    # try/except -- a row with an EMPTY "tête_de_tête" field parses as ''
    # via csv.DictReader (literal_eval('') raises, silently dumping the
    # whole row into "Autre" even when "tête" itself is valid), but as
    # None via polars (skips literal_eval, no exception). Must read with
    # polars to match the convention classify_relation was validated against.
    df = pl.read_csv(path, separator="\t", infer_schema_length=0)
    rows = list(df.iter_rows(named=True))
    prix_rows = [r for r in rows if r["fichier"] in prix_novels]
    total_all = len(rows)
    total_prix = len(prix_rows)
    from collections import Counter
    cats_all = Counter(classify_relation(r) for r in rows)
    cats_prix = Counter(classify_relation(r) for r in prix_rows)
    print(f"\n{'='*60}\n  TASK 3 — {label} — Prix du roman d'écologie (47 novels)\n{'='*60}")
    print(f"  Total mentions (all corpus): {total_all:,}")
    print(f"  Total mentions (Prix subcorpus only): {total_prix:,}  ({total_prix/total_all*100:.1f}% of corpus total)")
    for cat in ("Agent actif", "Récepteur passif", "Objet", "Complément du nom", "Autre"):
        n_all = cats_all.get(cat, 0)
        n_prix = cats_prix.get(cat, 0)
        pct_all = n_all / total_all * 100 if total_all else 0
        pct_prix = n_prix / total_prix * 100 if total_prix else 0
        print(f"  {cat:<18} all-corpus: {n_all:>7,} ({pct_all:5.1f}%)   Prix-only: {n_prix:>6,} ({pct_prix:5.1f}%)")
    return total_prix, cats_prix


def main():
    prix_novels = load_prix_novels()
    print(f"Prix du roman d'écologie subcorpus: {len(prix_novels)} novels")

    task1_breakout(TASK1_ANIMAUX, "ANIMAUX", prix_novels)
    task1_breakout(TASK1_PLANTES, "PLANTES", prix_novels)
    task3_breakout(TASK3_ANIMAUX, "ANIMAUX référentiels", prix_novels)
    task3_breakout(TASK3_PLANTES, "PLANTES référentiels", prix_novels)


if __name__ == "__main__":
    main()
