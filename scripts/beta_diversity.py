"""
Beta diversity: Jaccard (presence/absence) and Bray-Curtis (abundance-
weighted) dissimilarity, (1) year-over-year vs. a 2001 baseline within a
corpus, and (2) between the 3 main corpora as pooled wholes.

Complete dataset + per-category (animaux/plantes/champignons/loterre/taxons,
each separate per Riccardo's 2026-10-22 confirmation — fungi and taxons are
NOT grouped with plants/Loterre).
"""
import csv
import os
from collections import Counter

csv.field_size_limit(10_000_000)

ENTITES_PRINCIPAL = os.path.expanduser("~/ecopoetique/resultats/corpus_principal/ENTITES_TOTAL.csv")
ENTITES_BESTSELLERS = os.path.expanduser("~/ecopoetique/resultats/bestsellers/BESTSELLERS_ENTITES_MERGED.csv")

CATEGORIES = {
    'global': None,
    'animaux': {'animal'},
    'plantes': {'plante'},
    'champignons': {'champignon'},
    'loterre': {'loterre'},
    'taxons': {'taxon'},
}


def load_entities(path):
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def pooled_community(entity_rows, file_set, source_filter=None):
    counts = Counter()
    for r in entity_rows:
        if r['fichier'] not in file_set:
            continue
        if source_filter is not None and r['source'] not in source_filter:
            continue
        counts[r['lemme']] += 1
    return counts


def jaccard(c1, c2):
    s1, s2 = set(c1), set(c2)
    inter, union = len(s1 & s2), len(s1 | s2)
    return 1 - (inter / union if union else 0)


def bray_curtis(c1, c2):
    species = set(c1) | set(c2)
    num = sum(abs(c1.get(s, 0) - c2.get(s, 0)) for s in species)
    den = sum(c1.get(s, 0) + c2.get(s, 0) for s in species)
    return num / den if den else 0


def load_year_map(meta_file):
    with open(meta_file, encoding='utf-8') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    return {r['File']: int(r['Year']) for r in rows if r['Year'].strip().isdigit()}


def year_over_year(entity_rows, meta_file, label, out_rows):
    year_map = load_year_map(meta_file)
    years = sorted(set(year_map.values()))
    baseline_year = years[0]

    for cat, sources in CATEGORIES.items():
        baseline_files = {f for f, y in year_map.items() if y == baseline_year}
        baseline_comm = pooled_community(entity_rows, baseline_files, sources)
        print(f"[{label}/{cat}] baseline year={baseline_year}, "
              f"{sum(baseline_comm.values())} mentions, {len(baseline_comm)} especes")

        for y in years:
            year_files = {f for f, yy in year_map.items() if yy == y}
            comm = pooled_community(entity_rows, year_files, sources)
            jac = jaccard(baseline_comm, comm)
            bc = bray_curtis(baseline_comm, comm)
            n_mentions = sum(comm.values())
            out_rows.append({'corpus': label, 'category': cat, 'year': y,
                              'baseline_year': baseline_year, 'n_novels': len(year_files),
                              'n_mentions': n_mentions, 'n_especes': len(comm),
                              'jaccard_vs_baseline': jac, 'braycurtis_vs_baseline': bc})
        print(f"  done {len(years)} years for {label}/{cat}")


def between_corpora(all_entity_rows, all_file_sets, out_rows):
    for cat, sources in CATEGORIES.items():
        communities = {name: pooled_community(all_entity_rows[name], all_file_sets[name], sources)
                       for name in all_entity_rows}
        names = list(communities.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                jac = jaccard(communities[a], communities[b])
                bc = bray_curtis(communities[a], communities[b])
                print(f"  [{cat}] {a} vs {b}: Jaccard={jac:.3f}, BrayCurtis={bc:.3f}")
                out_rows.append({'category': cat, 'corpus_a': a, 'corpus_b': b,
                                  'jaccard': jac, 'braycurtis': bc})


def main():
    principal_rows = load_entities(ENTITES_PRINCIPAL)
    bestsellers_rows = load_entities(ENTITES_BESTSELLERS)

    with open(os.path.expanduser('~/ecopoetique/corpus_DigEco.csv'), encoding='utf-8') as f:
        digeco_files = {r['File'] for r in csv.DictReader(f, delimiter='\t')}
    with open(os.path.expanduser('~/ecopoetique/corpus_Bestsellers.csv'), encoding='utf-8') as f:
        best_files = {r['File'] for r in csv.DictReader(f, delimiter='\t')}
    with open(os.path.expanduser('~/ecopoetique/corpus_PRIX_ECOLOGIE.csv'), encoding='utf-8') as f:
        prix_files = {r['File'] for r in csv.DictReader(f, delimiter='\t')}

    print("=" * 60)
    print("YEAR-OVER-YEAR vs EARLIEST-AVAILABLE-YEAR BASELINE (per category)")
    print("=" * 60)
    yoy_rows = []
    year_over_year(principal_rows, os.path.expanduser('~/ecopoetique/corpus_DigEco.csv'),
                    'DigEco', yoy_rows)
    year_over_year(bestsellers_rows, os.path.expanduser('~/ecopoetique/corpus_Bestsellers.csv'),
                    'Bestsellers', yoy_rows)
    # PRIX_ECOLOGIE has no novels before 2017, so "2001 onwards" doesn't apply —
    # year_over_year() auto-detects the earliest available year as its own
    # baseline (2017 here), giving the same kind of temporal analysis using
    # this corpus's real start year instead of leaving it out entirely.
    year_over_year(principal_rows, os.path.expanduser('~/ecopoetique/corpus_PRIX_ECOLOGIE.csv'),
                    'PRIX_ECOLOGIE', yoy_rows)

    print()
    print("=" * 60)
    print("BETWEEN THE 3 MAIN CORPORA (per category)")
    print("=" * 60)
    all_entity_rows = {'DigEco': principal_rows, 'Bestsellers': bestsellers_rows, 'PRIX_ECOLOGIE': principal_rows}
    all_file_sets = {'DigEco': digeco_files, 'Bestsellers': best_files, 'PRIX_ECOLOGIE': prix_files}
    between_rows = []
    between_corpora(all_entity_rows, all_file_sets, between_rows)

    out_dir = os.path.expanduser('~/ecopoetique/resultats/biodiversite')
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'beta_diversity_year_over_year.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['corpus', 'category', 'year', 'baseline_year', 'n_novels',
                                           'n_mentions', 'n_especes', 'jaccard_vs_baseline',
                                           'braycurtis_vs_baseline'])
        w.writeheader()
        w.writerows(yoy_rows)
    with open(os.path.join(out_dir, 'beta_diversity_between_corpora.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['category', 'corpus_a', 'corpus_b', 'jaccard', 'braycurtis'])
        w.writeheader()
        w.writerows(between_rows)
    print(f"\nSaved to {out_dir}/beta_diversity_year_over_year.csv and beta_diversity_between_corpora.csv")


if __name__ == '__main__':
    main()
