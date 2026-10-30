"""
Genuinely different Task 2 technique: RETRIEVAL-based few-shot, not static.
Every static few-shot variant tonight (generic, META_NOM-targeted,
comprehensive) showed the SAME fixed examples to every input and netted to
a wash. This instead builds a small bank of rule-certain canonical examples
(SUBCATEGORIES' own phrases, zero leakage) and, for each new input, embeds
both the bank and the input via spaCy word vectors, retrieving only the
1-2 MOST SIMILAR examples to show — a different, input-specific prompt each
time, not one static block everyone sees.
"""
import csv, sys, os, time
import numpy as np
import spacy

sys.path.insert(0, os.path.dirname(__file__))
import run_task2_subcategories as t2
from spacy_syntax_classifier import classify_syntax

t2.OLLAMA_URL = "http://127.0.0.1:11460/api/chat"

nlp = spacy.load("fr_core_news_lg")

# Canonical bank: SUBCATEGORIES' own built-in examples, zero leakage risk.
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


def retrieve_examples(context, k=2):
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
        for phrase, cat, reason in examples
    )
    base = t2.make_prompt(token, context, category)
    intro_end = base.index("Détermine la catégorie")
    return (base[:intro_end] +
            f"EXEMPLES PERTINENTS (retrouvés pour ce cas précis) :\n\n{ex_block}\n\n" +
            base[intro_end:])


def main():
    with open("gold_task2_task45_CURRENT.csv", encoding="utf-8") as f:
        gold = list(csv.DictReader(f, delimiter=";"))
    for r in gold:
        if r["subcategorie_metaphore"].strip().upper() == "META_ATT":
            r["subcategorie_metaphore"] = "META_NOM"
    rows = [r for r in gold if r["subcategorie_metaphore"].strip() in t2.VALID_CODES]
    print(f"Usable rows: {len(rows)}")

    OUTPUT_FILE = "resultats_task2_retrieval_idiomfix_FINAL_184.csv"
    done_ids = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
            done_ids = {r["id"] for r in existing if r.get("predicted", "ERROR") != "ERROR"}
        print(f"Resuming: {len(done_ids)} already done")

    fields = ["id", "token_lexique", "gold", "predicted", "method", "correct"]
    write_header = not os.path.exists(OUTPUT_FILE) or len(done_ids) == 0
    out_f = open(OUTPUT_FILE, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=fields)
    if write_header:
        writer.writeheader()

    remaining = [r for r in rows if r["id"] not in done_ids]
    print(f"Remaining: {len(remaining)}")

    correct = 0
    start = time.time()
    for i, r in enumerate(remaining, 1):
        token = r["token_lexique"].strip()
        ctx = r["contexte"].strip()
        cat = r.get("source", "").strip()
        gold_cat = r["subcategorie_metaphore"].strip().upper()

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

        ok = (code == gold_cat)
        correct += ok
        writer.writerow({"id": r["id"], "token_lexique": token, "gold": gold_cat,
                          "predicted": code, "method": method, "correct": ok})
        out_f.flush()

        if i % 10 == 0 or i == len(remaining):
            elapsed = time.time() - start
            print(f"  [{i}/{len(remaining)}] correct={correct} elapsed={elapsed/60:.1f}min")

    out_f.close()
    total = len(rows)
    print(f"\nDone. {correct}/{total} = {correct/total*100:.1f}%. See {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
