"""
Task 1 — Loterre full-corpus run (climate-change/Anthropocene terminology).
Uses the exact v8 prompt (85.2% gold accuracy, finalized 2026-06-24) unchanged
— imported directly from evaluate_loterre_v8.py rather than re-described, per
the project's own standing lesson (always reuse the exact validated prompt
function for a production run, never redescribe it from scratch).

Input:  resultats/corpus_principal/ENTITES_contexte_loterre.csv +
        resultats/bestsellers/BESTSELLERS_contexte_loterre.csv (combined,
        ~130,572 candidate rows)
Output: resultats/task1_loterre_labels.csv
Resume-safe: checkpoints every row, skips already-done (fichier, token,
contexte[:50]) keys on restart — this run is expected to take ~5 days, so
surviving interruption is essential, not optional.
"""
import csv, sys, os, time
csv.field_size_limit(10_000_000)
sys.path.insert(0, os.path.dirname(__file__))
import evaluate_loterre_v8 as loterre
loterre.OLLAMA_URL = "http://127.0.0.1:11436/api/chat"  # dedicated instance, own GPU

INPUT_FILES = [
    os.path.expanduser("~/ecopoetique/resultats/corpus_principal/ENTITES_contexte_loterre.csv"),
    os.path.expanduser("~/ecopoetique/resultats/bestsellers/BESTSELLERS_contexte_loterre.csv"),
]
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/resultats/task1_loterre_labels.csv")

def main():
    rows = []
    for path in INPUT_FILES:
        with open(path, encoding="utf-8") as f:
            rows.extend(list(csv.DictReader(f, delimiter="\t")))
    print(f"Total candidate rows: {len(rows)}")

    done_keys = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = list(csv.DictReader(f, delimiter="\t"))
        # found 2026-10-16: a hard process kill mid-write can leave a
        # truncated trailing row (fields parse as None) — skip any row
        # that isn't fully formed rather than crashing on resume.
        existing = [r for r in existing if r.get("fichier") and r.get("token_lexique") and r.get("contexte") is not None]
        done_keys = {(r["fichier"], r["token_lexique"], r["contexte"][:50]) for r in existing}
        print(f"Already done: {len(done_keys)} — resuming")

    fields = ["fichier", "token_lexique", "contexte", "lemme", "categorie", "task1_label"]
    write_header = not os.path.exists(OUTPUT_FILE) or len(done_keys) == 0
    out_f = open(OUTPUT_FILE, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=fields, delimiter="\t")
    if write_header:
        writer.writeheader()

    remaining = [r for r in rows if (r["fichier"], r["token_lexique"], r["contexte"][:50]) not in done_keys]
    print(f"Remaining: {len(remaining)}")

    start = time.time()
    for i, r in enumerate(remaining, 1):
        token = r["token_lexique"].strip()
        ctx = r["contexte"].strip()
        pred = loterre.classify(token, ctx)
        if pred is None:
            # 2026-10-28: do NOT write a blind fallback label here. A prior
            # version silently wrote "référentiel" on any classify() failure
            # (timeout, 500 error, connection drop) and still marked the row
            # done -- during today's server instability this corrupted
            # ~34,621 rows with a wrong default, permanently (the resume
            # logic never retries a row once it's in the output file).
            # Skip instead: leave the row genuinely unprocessed so the next
            # run's resume logic picks it up and actually retries it.
            print(f"    SKIP (classify failed, will retry next run): {token}")
            continue

        writer.writerow({
            "fichier": r["fichier"], "token_lexique": token, "contexte": ctx,
            "lemme": r.get("lemme", ""), "categorie": r.get("categorie", ""),
            "task1_label": pred,
        })
        out_f.flush()

        if i % 50 == 0 or i == len(remaining):
            elapsed = time.time() - start
            seen = len(done_keys) + i
            rate = i / elapsed if elapsed > 0 else 0
            eta_h = (len(remaining) - i) / rate / 3600 if rate > 0 else float("inf")
            print(f"  [{i}/{len(remaining)} this run, {seen} total] elapsed={elapsed/3600:.2f}h eta={eta_h:.1f}h")

    out_f.close()
    print(f"\nDone. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
