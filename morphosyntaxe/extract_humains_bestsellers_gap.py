"""
Closes Task 3's humans bestsellers coverage gap (2026-10-20): dépendants_HUMAINS.csv
only ever covered CORPUS_TOTAL (corpus_principal, 925 novels) — the 88-novel
bestsellers subset was never run through extract_humains.py at all (0/88),
the same class of gap already found and fixed for animals and plants on
2026-07-08, just never applied to humans. Reuses process_novel() from
extract_humains.py directly (same head/head-of-head logic, same fr_core_news_lg
model) rather than re-describing it, per the project's own standing lesson.
Appends to the existing dépendants_HUMAINS.csv rather than overwriting it.
"""
import os, csv, time, sys
sys.path.insert(0, os.path.dirname(__file__))
import extract_humains as eh

BESTSELLERS_DIR = os.path.expanduser("~/ecopoetique/CORPUS_Bestsellers")
OUTPUT_FILE = eh.OUTPUT_FILE  # dépendants_HUMAINS.csv, append in place

def main():
    corpus_files = sorted(
        os.path.join(BESTSELLERS_DIR, f) for f in os.listdir(BESTSELLERS_DIR) if f.endswith(".txt")
    )
    print(f"Processing {len(corpus_files)} bestsellers novels...")
    print(f"Appending to: {OUTPUT_FILE}")

    fieldnames = ["fichier", "token_lexique", "truncated_sentence", "lemme",
                  "genre", "tête", "tête_de_tête", "rôle"]

    start_time = time.time()
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        total_rows = 0
        for i, filepath in enumerate(corpus_files, 1):
            fname = os.path.basename(filepath)
            rows = eh.process_novel(filepath)
            if rows:
                writer.writerows(rows)
                f.flush()
                total_rows += len(rows)
            elapsed = time.time() - start_time
            eta = (elapsed / i) * (len(corpus_files) - i)
            print(f"  [{i:>3}/{len(corpus_files)}] {fname[:50]:<50} "
                  f"+{len(rows):>4} rows | total={total_rows:>7,} | ETA={eta/60:.0f}min")

    print(f"\nDone. Added {total_rows:,} rows for {len(corpus_files)} bestsellers novels.")

if __name__ == "__main__":
    main()
