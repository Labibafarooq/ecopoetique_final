"""
Hill numbers: q=0 (richness), q=1 (exp(Shannon)), q=2 (inverse Simpson).

Per-book: computed from the SAME rarefied Monte Carlo samples as the already-
done Shannon/Pielou work (same size parameter, same trial loop) — consistency
matters here since book lengths vary wildly, the exact reason Shannon used
rarefaction in the first place.

Per-corpus and per-year: computed directly on the full pooled abundance data,
NOT rarefied — these aggregates already have thousands of mentions, so
rarefying down to 20-50 individuals would discard almost all information
instead of correcting a length bias. Judgment call, flagged to the user.
"""
import sys
import random
import csv
import os
from collections import Counter

csv.field_size_limit(10_000_000)

CATEGORIES = {
    'global': None,
    'animaux': {'animal'},
    'plantes': {'plante'},
    'champignons': {'champignon'},
    'loterre': {'loterre'},
    'taxons': {'taxon'},
}


def hill_numbers_from_counts(counts):
    """q=0,1,2 Hill numbers from a raw abundance Counter (no rarefaction)."""
    total = sum(counts.values())
    if total == 0:
        return None, None, None
    q0 = len(counts)
    proportions = [v / total for v in counts.values()]
    shannon_h = -sum(p * __import__('math').log(p) for p in proportions if p > 0)
    q1 = __import__('math').exp(shannon_h)
    simpson = sum(p ** 2 for p in proportions)
    q2 = 1 / simpson if simpson > 0 else None
    return q0, q1, q2


def hill_numbers_rarefied(population, size, trials=30):
    if len(population) < size:
        return None, None, None
    q0s, q1s, q2s = [], [], []
    for _ in range(trials):
        sample = random.sample(population, size)
        counts = Counter(sample)
        q0, q1, q2 = hill_numbers_from_counts(counts)
        q0s.append(q0)
        q1s.append(q1)
        q2s.append(q2)
    return (sum(q0s) / len(q0s), sum(q1s) / len(q1s), sum(q2s) / len(q2s))


def pooled_community(entity_rows, file_set, source_filter=None):
    counts = Counter()
    for r in entity_rows:
        if r['fichier'] not in file_set:
            continue
        if source_filter is not None and r['source'] not in source_filter:
            continue
        counts[r['lemme']] += 1
    return counts


def per_book(entities_file, meta_file, size):
    with open(entities_file, encoding='utf-8') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    by_file = {}
    for r in rows:
        by_file.setdefault(r['fichier'], []).append(r)

    results = {cat: {} for cat in CATEGORIES}
    for filename, filerows in by_file.items():
        for cat, sources in CATEGORIES.items():
            pop = [r['lemme'] for r in filerows if sources is None or r['source'] in sources]
            results[cat][filename] = hill_numbers_rarefied(pop, size)

    with open(meta_file, encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        fieldnames = list(reader.fieldnames)
        meta_rows = list(reader)

    new_cols = []
    for cat in CATEGORIES:
        suffix = '' if cat == 'global' else f'_{cat}'
        for q in [0, 1, 2]:
            new_cols.append(f'Hill_q{q}_{size}{suffix}')
    for col in new_cols:
        if col not in fieldnames:
            fieldnames.append(col)

    for row in meta_rows:
        fn = row['File']
        for cat in CATEGORIES:
            suffix = '' if cat == 'global' else f'_{cat}'
            q0, q1, q2 = results[cat].get(fn, (None, None, None))
            row[f'Hill_q0_{size}{suffix}'] = '' if q0 is None else q0
            row[f'Hill_q1_{size}{suffix}'] = '' if q1 is None else q1
            row[f'Hill_q2_{size}{suffix}'] = '' if q2 is None else q2

    with open(meta_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(meta_rows)
    print(f"Per-book Hill numbers (size={size}) written to {meta_file}")


def per_corpus_and_year(entities_file, meta_file, corpus_label, out_rows):
    with open(entities_file, encoding='utf-8') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    with open(meta_file, encoding='utf-8') as f:
        meta_rows = list(csv.DictReader(f, delimiter='\t'))
    all_files = {r['File'] for r in meta_rows}
    year_map = {r['File']: int(r['Year']) for r in meta_rows if r['Year'].strip().isdigit()}

    for cat, sources in CATEGORIES.items():
        comm = pooled_community(rows, all_files, sources)
        q0, q1, q2 = hill_numbers_from_counts(comm)
        out_rows.append({'scope': 'corpus', 'label': corpus_label, 'category': cat,
                          'n_mentions': sum(comm.values()), 'Hill_q0': q0, 'Hill_q1': q1, 'Hill_q2': q2})

    years = sorted(set(year_map.values()))
    for y in years:
        year_files = {f for f, yy in year_map.items() if yy == y}
        for cat, sources in CATEGORIES.items():
            comm = pooled_community(rows, year_files, sources)
            q0, q1, q2 = hill_numbers_from_counts(comm)
            out_rows.append({'scope': 'year', 'label': f'{corpus_label}_{y}', 'category': cat,
                              'n_mentions': sum(comm.values()), 'Hill_q0': q0, 'Hill_q1': q1, 'Hill_q2': q2})
    print(f"Corpus+year Hill numbers computed for {corpus_label}")


if __name__ == '__main__':
    ENTITES_PRINCIPAL = os.path.expanduser("~/ecopoetique/resultats/corpus_principal/ENTITES_TOTAL.csv")
    ENTITES_BESTSELLERS = os.path.expanduser("~/ecopoetique/resultats/bestsellers/BESTSELLERS_ENTITES_MERGED.csv")
    DIGECO = os.path.expanduser("~/ecopoetique/corpus_DigEco.csv")
    BESTSELLERS = os.path.expanduser("~/ecopoetique/corpus_Bestsellers.csv")
    PRIX = os.path.expanduser("~/ecopoetique/corpus_PRIX_ECOLOGIE.csv")

    for size in [20, 50]:
        per_book(ENTITES_PRINCIPAL, DIGECO, size)
        per_book(ENTITES_PRINCIPAL, PRIX, size)
        per_book(ENTITES_BESTSELLERS, BESTSELLERS, size)

    out_rows = []
    per_corpus_and_year(ENTITES_PRINCIPAL, DIGECO, 'DigEco', out_rows)
    per_corpus_and_year(ENTITES_BESTSELLERS, BESTSELLERS, 'Bestsellers', out_rows)
    per_corpus_and_year(ENTITES_PRINCIPAL, PRIX, 'PRIX_ECOLOGIE', out_rows)

    out_dir = os.path.expanduser('~/ecopoetique/resultats/biodiversite')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'hill_numbers_corpus_year.csv')
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['scope', 'label', 'category', 'n_mentions', 'Hill_q0', 'Hill_q1', 'Hill_q2'])
        w.writeheader()
        w.writerows(out_rows)
    print(f"Saved corpus/year Hill numbers to {out_path}")
