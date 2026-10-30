"""
Species Abundance Distribution (SAD) per corpus: empirical SAD, log-series
and log-normal fits, AIC/BIC comparison, rank-abundance + Preston plots.

Usage:
    python3 sad_fit.py <ENTITES_file> <corpus_metadata.csv> <corpus_label> <out_dir> [source_filter_csv]

source_filter_csv is optional: comma-separated list of 'source' values to
restrict to (e.g. "animal" or "plante,champignon"). Omit for the complete
dataset (all sources combined).
"""
import sys
import csv
import os
import numpy as np
from collections import Counter
from scipy.optimize import brentq
from scipy.stats import lognorm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

csv.field_size_limit(10_000_000)

ENTITES_FILE, META_FILE, LABEL, OUT_DIR = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
SOURCE_FILTER = set(sys.argv[5].split(',')) if len(sys.argv) > 5 else None

os.makedirs(OUT_DIR, exist_ok=True)


def load_abundances(entites_file, meta_file, source_filter):
    with open(meta_file, encoding='utf-8') as f:
        corpus_files = set(r['File'] for r in csv.DictReader(f, delimiter='\t'))
    with open(entites_file, encoding='utf-8') as f:
        rows = csv.DictReader(f, delimiter='\t')
        counts = Counter()
        for r in rows:
            if r['fichier'] not in corpus_files:
                continue
            if source_filter is not None and r['source'] not in source_filter:
                continue
            counts[r['lemme']] += 1
    return counts


def fit_logseries(abundances):
    """Fisher's log-series MLE. p(n) = -x^n / (n * ln(1-x)), n=1,2,...
    Given S (richness) and N (total individuals), x solves:
        S/N = -(1-x) * ln(1-x) / x
    """
    N = sum(abundances)
    S = len(abundances)

    def eq(x):
        return -(1 - x) * np.log(1 - x) / x - S / N

    x = brentq(eq, 1e-10, 1 - 1e-10)
    alpha = N * (1 - x) / x

    loglik = 0.0
    for n in abundances:
        p_n = -x ** n / (n * np.log(1 - x))
        loglik += np.log(p_n)
    return {'x': x, 'alpha': alpha, 'loglik': loglik, 'k': 1, 'N': N, 'S': S}


def fit_lognormal(abundances):
    """2-parameter log-normal fit on raw abundances (continuous approximation,
    standard simplified practice for comparing against log-series via AIC/BIC)."""
    abundances = np.array(abundances, dtype=float)
    shape, loc, scale = lognorm.fit(abundances, floc=0)
    loglik = np.sum(lognorm.logpdf(abundances, shape, loc=0, scale=scale))
    return {'shape': shape, 'scale': scale, 'loglik': loglik, 'k': 2}


def aic(loglik, k):
    return 2 * k - 2 * loglik


def bic(loglik, k, n):
    return k * np.log(n) - 2 * loglik


def rank_abundance_plot(abundances, label, out_path):
    sorted_ab = sorted(abundances, reverse=True)
    plt.figure(figsize=(6, 4.5))
    plt.plot(range(1, len(sorted_ab) + 1), sorted_ab, marker='o', markersize=2, linewidth=0.8)
    plt.yscale('log')
    plt.xlabel('Rang de l\'espèce')
    plt.ylabel('Abondance (log)')
    plt.title(f'Rank-abundance — {label}')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def preston_plot(abundances, label, out_path):
    abundances = np.array(abundances)
    octaves = np.floor(np.log2(abundances)).astype(int)
    max_oct = octaves.max()
    bins = np.arange(0, max_oct + 2)
    counts, _ = np.histogram(octaves, bins=bins)
    plt.figure(figsize=(6, 4.5))
    plt.bar(bins[:-1], counts, width=0.9, align='edge')
    labels = [f'{2**b}-{2**(b+1)-1}' for b in bins[:-1]]
    plt.xticks(bins[:-1] + 0.45, labels, rotation=45, ha='right', fontsize=7)
    plt.xlabel('Classe d\'abondance (octaves, Preston)')
    plt.ylabel('Nombre d\'espèces')
    plt.title(f'Preston plot — {label}')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def main():
    counts = load_abundances(ENTITES_FILE, META_FILE, SOURCE_FILTER)
    abundances = [v for v in counts.values() if v > 0]
    N, S = sum(abundances), len(abundances)
    print(f"[{LABEL}] N={N} individus, S={S} especes")

    ls = fit_logseries(abundances)
    ln = fit_lognormal(abundances)

    ls_aic, ls_bic = aic(ls['loglik'], ls['k']), bic(ls['loglik'], ls['k'], S)
    ln_aic, ln_bic = aic(ln['loglik'], ln['k']), bic(ln['loglik'], ln['k'], S)

    print(f"  log-series : x={ls['x']:.4f} alpha={ls['alpha']:.2f} logL={ls['loglik']:.1f} AIC={ls_aic:.1f} BIC={ls_bic:.1f}")
    print(f"  log-normal : shape={ln['shape']:.4f} scale={ln['scale']:.2f} logL={ln['loglik']:.1f} AIC={ln_aic:.1f} BIC={ln_bic:.1f}")
    winner = 'log-series' if ls_aic < ln_aic else 'log-normal'
    print(f"  -> meilleur modele (AIC): {winner}")

    safe_label = LABEL.replace(' ', '_').replace('/', '_')
    rank_abundance_plot(abundances, LABEL, os.path.join(OUT_DIR, f'rankabundance_{safe_label}.png'))
    preston_plot(abundances, LABEL, os.path.join(OUT_DIR, f'preston_{safe_label}.png'))

    summary_path = os.path.join(OUT_DIR, 'sad_summary.csv')
    file_exists = os.path.exists(summary_path)
    with open(summary_path, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(['label', 'N', 'S', 'ls_x', 'ls_alpha', 'ls_loglik', 'ls_AIC', 'ls_BIC',
                        'ln_shape', 'ln_scale', 'ln_loglik', 'ln_AIC', 'ln_BIC', 'best_model'])
        w.writerow([LABEL, N, S, ls['x'], ls['alpha'], ls['loglik'], ls_aic, ls_bic,
                    ln['shape'], ln['scale'], ln['loglik'], ln_aic, ln_bic, winner])
    print(f"  saved plots + appended summary to {OUT_DIR}")


if __name__ == '__main__':
    main()
