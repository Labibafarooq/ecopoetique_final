"""
Recalcule Shannon (rarefie) et Pielou, pour tout le dataset et par categorie
taxonomique (animaux / plantes+champignons / loterre+taxons), a partir des
fichiers d'entites AJOUR (incluant le correctif formes-derivees-animaux
d'octobre 2026). Remplace proprement les anciennes colonnes figees.

Usage:
    python3 shannon_pielou_recalc.py <ENTITES_TOTAL.csv> <FICHIER_METADONNEES.csv> <taille_rarefaction>
"""
import sys
import random
import csv
from collections import Counter
from math import log
from scipy.stats import entropy

csv.field_size_limit(10_000_000)

ENTITES_TOTAL, FICHIER_METADONNEES, SIZE = sys.argv[1], sys.argv[2], int(sys.argv[3])
TRIALS = 30

CATEGORIES = {
    'global': None,
    'animaux': {'animal'},
    'plantes': {'plante'},
    'champignons': {'champignon'},
    'loterre': {'loterre'},
    'taxons': {'taxon'},
}


def shannon_and_richness_rarefied(population, size, trials=TRIALS):
    if len(population) < size:
        return None, None
    H_values, S_values = [], []
    for _ in range(trials):
        sample = random.sample(population, size)
        counts = Counter(sample)
        proportions = [v / size for v in counts.values()]
        H_values.append(entropy(proportions))
        S_values.append(len(counts))
    H = sum(H_values) / len(H_values)
    S = sum(S_values) / len(S_values)
    return H, S


def pielou(H, S):
    if H is None or S is None or S <= 1:
        return None
    return H / log(S)


with open(ENTITES_TOTAL, encoding='utf-8') as f:
    rows = list(csv.DictReader(f, delimiter='\t'))

by_file = {}
for r in rows:
    by_file.setdefault(r['fichier'], []).append(r)

results = {cat: {} for cat in CATEGORIES}

for filename, filerows in by_file.items():
    for cat, sources in CATEGORIES.items():
        pop = [r['lemme'] for r in filerows if sources is None or r['source'] in sources]
        H, S = shannon_and_richness_rarefied(pop, SIZE)
        J = pielou(H, S)
        results[cat][filename] = (H, J)

with open(FICHIER_METADONNEES, encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    fieldnames = list(reader.fieldnames)
    meta_rows = list(reader)

new_cols = []
for cat in CATEGORIES:
    suffix = '' if cat == 'global' else f'_{cat}'
    new_cols.append(f'Shannon_rarefied_{SIZE}{suffix}')
    new_cols.append(f'Pielou_{SIZE}{suffix}')

for col in new_cols:
    if col not in fieldnames:
        fieldnames.append(col)

for row in meta_rows:
    fn = row['File']
    for cat in CATEGORIES:
        suffix = '' if cat == 'global' else f'_{cat}'
        H, J = results[cat].get(fn, (None, None))
        row[f'Shannon_rarefied_{SIZE}{suffix}'] = '' if H is None else H
        row[f'Pielou_{SIZE}{suffix}'] = '' if J is None else J

with open(FICHIER_METADONNEES, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
    writer.writeheader()
    writer.writerows(meta_rows)

n_computed = sum(1 for fn in results['global'] if results['global'][fn][0] is not None)
print(f"Done. size={SIZE}, {len(by_file)} fichiers vus, {n_computed} avec Shannon global calcule.")
print(f"Colonnes ecrites dans {FICHIER_METADONNEES}: {new_cols}")
