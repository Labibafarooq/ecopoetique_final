"""
Task 2, full-corpus run. Same retrieval-fewshot technique validated on the
184-row gold set (76.7% honest test-set accuracy, 102-entry idiom lexicon
after today's web/corpus-sourced expansion), now applied to every real
figurative mention in the corpus (figuratifs_task1_own.csv, ~44,956 rows
after excluding the 184/200 gold rows already scored).

No gold label exists at this scale, so this writes predictions only (no
"correct" column). Split into 2 halves (--half 1 / --half 2) to run on
2 GPUs in parallel. Resume-safe: checkpoints by row, skips done keys.
"""
import csv, sys, os, time, argparse
import numpy as np
import spacy

sys.path.insert(0, os.path.dirname(__file__))
import run_task2_subcategories as t2
from spacy_syntax_classifier import classify_syntax

parser = argparse.ArgumentParser()
parser.add_argument("--half", type=int, required=True, choices=[1, 2])
parser.add_argument("--port", type=int, required=True)
args = parser.parse_args()

t2.OLLAMA_URL = f"http://127.0.0.1:{args.port}/api/chat"

nlp = spacy.load("fr_core_news_lg")

BANK = [
    ("cet homme est un loup", "META_NOM", "copule établit une IDENTITé directe, sans complément de"),
    ("cette ville est une fourmilière", "META_NOM", "copule, identité directe"),
    ("une mémoire d'éléphant", "META_QUAL", "N1 DE N2, N2 (éléphant) qualifie N1 (mémoire)"),
    ("une mer de soie", "META_QUAL", "N1 DE N2, N2 qualifie N1"),
    ("une forêt de pylônes", "META_DET", "N1 DE N2, N1 (forêt) métaphorise N2"),
    ("un essaim de pensées", "META_DET", "N1 DE N2, N1 métaphorise N2"),
    ("la montagne sentinelle", "META_APP", "apposition directe sans copule ni de"),
    ("le fleuve serpent", "META_APP", "apposition directe"),
    ("arbre-parapluie", "META_APP", "mot composé, apposition"),
    ("la forêt avalait la lumière", "META_PRED", "verbe d'action incompatible avec le sujet"),
    ("le glacier agonisait", "META_PRED", "verbe incompatible"),
    ("une douceur végétale", "META_PRED", "adjectif normalement étranger au sujet"),
    ("on aurait dit une meute de nuages", "MOD_ANALOG", "marqueur modal de ressemblance de surface"),
    ("bleu ciel", "COUL", "couleur + référent du vivant"),
    ("avoir la chair de poule", "LOC_IDIOM", "expression figée, sens non compositionnel"),
    ("poser un lapin", "LOC_IDIOM", "expression figée"),
    ("un tableau représentant un lion", "IMAG", "représentation visuelle"),
    ("une robe à fleurs", "IMAG", "motif décoratif"),
    ("rusé comme un renard", "COMP_SIM", "comme + trait statique sans action"),
    ("courir comme un lièvre", "COMP_SIM", "comme + trait statique"),
    ("les branches craquaient comme les os d'un vieux cerf", "COMP_P", "comme + processus/action subie"),
    ("plus lent qu'une tortue", "COMP_Q", "comparaison de degré explicite"),
    ("plus haut qu'un séquoia", "COMP_Q", "comparaison de degré"),
]
BANK_VECS = np.array([nlp(phrase).vector for phrase, _, _ in BANK])
BANK_NORMS = np.linalg.norm(BANK_VECS, axis=1, keepdims=True)
BANK_VECS_NORM = BANK_VECS / np.maximum(BANK_NORMS, 1e-8)


def retrieve_examples(context, k=4):
    vec = nlp(context).vector
    norm = np.linalg.norm(vec)
    if norm < 1e-8:
        return BANK[:k]
    vec_norm = vec / norm
    sims = BANK_VECS_NORM @ vec_norm
    top_idx = np.argsort(-sims)[:k]
    return [BANK[i] for i in top_idx]


def make_retrieval_prompt(token, context, category, examples):
    ex_block = "\n\n".join(
        f'EXEMPLE — «{phrase}»\nCatégorie correcte : {cat}\nRaison : {reason}'
        for phrase, cat, reason in examples)
    base = t2.make_prompt(token, context, category)
    intro_end = base.index("Détermine la catégorie")
    return (base[:intro_end] +
            f"EXEMPLES PERTINENTS (retrouvés pour ce cas précis) :\n\n{ex_block}\n\n" +
            base[intro_end:])


def row_key(fichier, token, contexte):
    return f"{fichier}|{token}|{contexte[:60]}"


def main():
    with open("gold_task2_task45_v2corrected.csv", encoding="utf-8") as f:
        gold_rows = list(csv.DictReader(f, delimiter=";"))
    gold_keys = {row_key(r["fichier"], r["token_lexique"], r["contexte"]) for r in gold_rows}

    with open("../figuratifs_task1_own.csv", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f, delimiter="\t"))

    fresh = [r for r in all_rows if row_key(r["fichier"], r["token_lexique"], r["contexte"]) not in gold_keys]
    fresh.sort(key=lambda r: (r["fichier"], r["token_lexique"]))

    mid = len(fresh) // 2
    my_rows = fresh[:mid] if args.half == 1 else fresh[mid:]
    print(f"Total full corpus (excl. gold): {len(fresh)}, this half ({args.half}): {len(my_rows)}")

    OUTPUT_FILE = f"resultats_task2_full_corpus_half{args.half}.csv"
    done_keys = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("predicted", "ERROR") != "ERROR":
                    done_keys.add(row_key(r["fichier"], r["token_lexique"], r["contexte"]))
        print(f"Resuming: {len(done_keys)} already done")

    fields = ["fichier", "token_lexique", "contexte", "categorie", "predicted", "method"]
    write_header = not os.path.exists(OUTPUT_FILE) or len(done_keys) == 0
    out_f = open(OUTPUT_FILE, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=fields)
    if write_header:
        writer.writeheader()

    remaining = [r for r in my_rows if row_key(r["fichier"], r["token_lexique"], r["contexte"]) not in done_keys]
    print(f"Remaining: {len(remaining)}")

    start = time.time()
    counts = {"rule": 0, "spacy": 0, "llm": 0}
    for i, r in enumerate(remaining, 1):
        token = r["token_lexique"].strip()
        ctx = r["contexte"].strip()
        cat = r.get("categorie", "").strip()

        code = t2.rule_based_classify(token, ctx)
        method = "rule"
        if code is None:
            spacy_pred, _ = classify_syntax(token, ctx)
            if spacy_pred is not None:
                code = spacy_pred
                method = "spacy"
        if code is None:
            examples = retrieve_examples(ctx, k=4)
            prompt = make_retrieval_prompt(token, ctx, cat, examples)
            code, _ = t2.call_ollama(prompt)
            method = "llm"
        counts[method] += 1

        writer.writerow({"fichier": r["fichier"], "token_lexique": token, "contexte": ctx,
                          "categorie": cat, "predicted": code, "method": method})
        out_f.flush()

        if i % 50 == 0 or i == len(remaining):
            elapsed = time.time() - start
            rate = i / elapsed if elapsed > 0 else 0
            eta_h = (len(remaining) - i) / rate / 3600 if rate > 0 else 0
            print(f"  [{i}/{len(remaining)}] elapsed={elapsed/60:.1f}min eta={eta_h:.1f}h counts={counts}", flush=True)

    out_f.close()
    print(f"\nHalf {args.half} done. {len(remaining)} rows written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
