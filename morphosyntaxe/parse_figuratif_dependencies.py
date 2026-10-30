"""
Dependency-parse the figurative (task1_label='figuré') animal and plant
mentions — same head/head-of-head logic as reparse_animaux_newforms.py /
reparse_plantes_missing.py (model fr_core_news_lg, consistent with the
existing référentiel dependency files), so results are directly comparable.

Never built before now — Task 3's agentivity analysis has only ever covered
référentiel mentions. This is step 1 of Riccardo's figurative-agentivity
request: build the dependency data so analyse_agentivite.py's classification
logic can be reused unchanged on the figurative subset.

Input:  figuratif_to_parse.tsv (fichier, token_lexique, truncated_sentence, lemme, source_cat)
Output: dépendants_animaux_figuratifs.csv, dépendants_plantes_figuratifs.csv
"""
import csv, os, sys, time
import spacy

csv.field_size_limit(10**7)

INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else \
    "/tmp/claude-46086/-raid-home-farooq-projects-ecopoetique-v2/ac85c010-f14e-4140-a228-4121563eecab/scratchpad/figuratif_to_parse.tsv"
OUT_ANIMAUX = os.path.expanduser("~/ecopoetique/morphosyntaxe/dépendants_animaux_figuratifs.csv")
OUT_PLANTES = os.path.expanduser("~/ecopoetique/morphosyntaxe/dépendants_plantes_figuratifs.csv")

nlp = spacy.load("fr_core_news_lg")


def get_dependencies(token_text, sentence):
    doc = nlp(sentence)
    match_text = token_text
    if " " in match_text or "-" in match_text:
        match_text = nlp(match_text)[0].text
    for token in doc:
        if token.text == match_text:
            head = (token.head.text, token.dep_)
            head_of_head = (token.head.head.text, token.head.dep_) if token.head != token else ("", "")
            return head, head_of_head
    return None, None


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    print(f"Rows to parse: {len(rows):,}")

    fieldnames = ["fichier", "token_lexique", "truncated_sentence", "lemme", "tête", "tête_de_tête"]
    f_animaux = open(OUT_ANIMAUX, "w", newline="", encoding="utf-8")
    f_plantes = open(OUT_PLANTES, "w", newline="", encoding="utf-8")
    w_animaux = csv.DictWriter(f_animaux, fieldnames=fieldnames, delimiter="\t")
    w_plantes = csv.DictWriter(f_plantes, fieldnames=fieldnames, delimiter="\t")
    w_animaux.writeheader()
    w_plantes.writeheader()

    matched = 0
    start = time.time()
    for i, r in enumerate(rows, 1):
        head, head_of_head = get_dependencies(r["token_lexique"], r["truncated_sentence"])
        if head is not None:
            matched += 1
        out_row = {
            "fichier": r["fichier"], "token_lexique": r["token_lexique"],
            "truncated_sentence": r["truncated_sentence"], "lemme": r["lemme"],
            "tête": str(head) if head is not None else "",
            "tête_de_tête": str(head_of_head) if head_of_head is not None else "",
        }
        if r["source_cat"] == "animal":
            w_animaux.writerow(out_row)
        else:
            w_plantes.writerow(out_row)

        if i % 1000 == 0 or i == len(rows):
            f_animaux.flush(); f_plantes.flush()
            elapsed = time.time() - start
            eta = (elapsed / i) * (len(rows) - i)
            print(f"  [{i:,}/{len(rows):,}] matched={matched:,} ({matched/i*100:.1f}%) "
                  f"elapsed={elapsed/60:.1f}min ETA={eta/60:.1f}min", flush=True)

    f_animaux.close(); f_plantes.close()
    print(f"\nDone. {matched:,}/{len(rows):,} matched ({matched/len(rows)*100:.1f}%)")
    print(f"Saved to: {OUT_ANIMAUX} and {OUT_PLANTES}")


if __name__ == "__main__":
    main()
