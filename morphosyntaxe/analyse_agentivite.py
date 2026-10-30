"""
Analyse d'agentivité — animaux et plantes référentiels
"""

import sys
import os
import polars as pl
from ast import literal_eval

# 2026-10-20: fix for the "passive-voice contamination" item flagged in
# task3_full_report.md ("likely mostly an être-auxiliary parsing artifact,
# confirmed real, never fixed"). Quantified against the real human data
# before fixing: 914/3231 (28.3%) of all nsubj:pass rows are governed by a
# French verb that simply takes être as its normal auxiliary (mourir, aller,
# venir, rester, naître, devenir, sortir, arriver, partir, entrer, rentrer,
# monter, descendre, retourner, parvenir — the classic "verbes qui se
# conjuguent avec être" set) or a pure être+adjective predicate (content,
# assis, triste...) — structurally identical to a passive to spaCy's parser,
# but not semantically passive (the subject isn't being acted on by anyone).
# "Likely mostly" turned out to overstate it: contamination is a real,
# substantial minority (28.3%), not most of the bucket — genuine passives
# (tué, arrêté, aimé, critiqué, accusé, blessé...) are still 71.7%.
# Reclassified as "Autre" rather than forced into "Agent actif" — these
# sentences aren't the subject acting on someone else either, just
# describing a state/event the subject underwent on their own.
_ETRE_AUX_OR_ADJ_PREDICATES = {
    "allé","allée","allés","allées",
    "venu","venue","venus","venues",
    "revenu","revenue","revenus","revenues",
    "devenu","devenue","devenus","devenues",
    "parvenu","parvenue","parvenus","parvenues",
    "arrivé","arrivée","arrivés","arrivées",
    "parti","partie","partis","parties",
    "entré","entrée","entrés","entrées",
    "sorti","sortie","sortis","sorties",
    "rentré","rentrée","rentrés","rentrées",
    "monté","montée","montés","montées",
    "descendu","descendue","descendus","descendues",
    "né","née","nés","nées",
    "mort","morte","morts","mortes",
    "resté","restée","restés","restées",
    "tombé","tombée","tombés","tombées",
    "retourné","retournée","retournés","retournées",
    "content","contente","contents","contentes",
    "assis","assise","assises",
    "debout","couché","couchée","couchés","couchées",
    "triste","tristes","heureux","heureuse","heureuses",
    "fier","fière","fiers","fières",
}

def classify_relation(row):
    try:
        tete = literal_eval(row["tête"]) if isinstance(row["tête"], str) else row["tête"]
        tete_de_tete = literal_eval(row["tête_de_tête"]) if isinstance(row["tête_de_tête"], str) else row["tête_de_tête"]
    except:
        return "Autre"
    rel = tete[1] if tete and len(tete) > 1 else None
    gov = tete[0] if tete and len(tete) > 1 else None
    if rel == "conj":
        rel = tete_de_tete[1] if tete_de_tete and len(tete_de_tete) > 1 else None
        gov = tete_de_tete[0] if tete_de_tete and len(tete_de_tete) > 1 else None
    if rel == "nsubj:pass" and gov and gov.lower() in _ETRE_AUX_OR_ADJ_PREDICATES:
        return "Autre"
    if rel in ["nsubj", "ROOT", "obl:agent"]: return "Agent actif"
    elif rel == "nsubj:pass": return "Récepteur passif"
    elif rel == "nmod": return "Complément du nom"
    elif rel == "obj": return "Objet"
    else: return "Autre"

def analyse_file(filepath, name):
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}"); return None
    df = pl.read_csv(filepath, separator='\t', infer_schema_length=0)
    total = len(df)
    categories = [classify_relation(row) for row in df.iter_rows(named=True)]
    df = df.with_columns(pl.Series("catégorie", categories))
    counts = df.group_by("catégorie").len().sort("len", descending=True)
    print(f"\n{'='*55}\n  {name}\n  Total: {total:,}\n{'='*55}")
    results = {}
    for row in counts.iter_rows():
        cat, n = row
        pct = n/total*100
        print(f"  {cat:<25} {n:>7,}  ({pct:>5.1f}%)  {'█'*int(pct/3)}")
        results[cat] = {"n": n, "pct": pct}
    print(f"\n  → Agent actif:     {results.get('Agent actif',{}).get('pct',0):.1f}%")
    print(f"  → Passif:          {results.get('Récepteur passif',{}).get('pct',0):.1f}%")
    print(f"  → Objet:           {results.get('Objet',{}).get('pct',0):.1f}%")
    return results, total

base = os.path.expanduser("~/ecopoetique/morphosyntaxe")
files = [
    (f"{base}/dépendants_HUMAINS.csv",              "HUMAINS (bestsellers gap closed, être-aux fix applied)"),
    (f"{base}/dépendants_animaux_référentiels_REFRESH.csv", "ANIMAUX référentiels (REFRESH, corrected labels, coverage-closed)"),
    (f"{base}/dépendants_plantes_référentiels_REFRESH.csv", "PLANTES référentiels (REFRESH, corrected labels, coverage-closed)"),
]

print("="*55)
print("ANALYSE D'AGENTIVITÉ — Écopoétique")
print("="*55)
all_results = {}
for fp, name in files:
    r = analyse_file(fp, name)
    if r: all_results[name] = r

print(f"\n{'='*55}\nRÉSUMÉ COMPARATIF\n{'='*55}")
print(f"  {'Catégorie':<30} {'Agent%':>7} {'Passif%':>8} {'Objet%':>7}")
print(f"  {'-'*52}")
for name, (res, total) in all_results.items():
    a = res.get("Agent actif",{}).get("pct",0)
    p = res.get("Récepteur passif",{}).get("pct",0)
    o = res.get("Objet",{}).get("pct",0)
    print(f"  {name:<30} {a:>6.1f}% {p:>7.1f}% {o:>6.1f}%")
