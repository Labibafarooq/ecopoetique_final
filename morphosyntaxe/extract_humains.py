"""
Extraction des personnages humains (PER) et analyse d'agentivité
Pour chaque personnage trouvé dans les romans:
  - Rôle syntaxique: Agent actif / Récepteur passif / Objet / Complément du nom
  - Genre: masculin / féminin / indéterminé
  - Contexte (phrase tronquée)

Output: ~/ecopoetique/morphosyntaxe/dépendants_HUMAINS.csv
"""

import os
import re
import csv
import spacy
import time
from pathlib import Path

CORPUS_DIR  = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/morphosyntaxe/dépendants_HUMAINS.csv")
MAX_CHARS   = 100000  # first 100k chars per novel (covers ~80 pages)
MAX_SENT_LEN = 150    # max chars for truncated sentence

# Known false positives to skip (publisher names, author names etc)
FALSE_POSITIVES = {
    "nord compo", "gallimard", "flammarion", "grasset", "seuil", "actes sud",
    "fayard", "albin michel", "stock", "minuit", "isbn", "p.", "dr",
}

nlp = spacy.load("fr_core_news_lg")

# ── Gender detection ────────────────────────────────────────────────────────

def detect_gender(token, doc):
    """Detect gender from morphology or nearby pronouns."""
    # From token morphology
    morph = token.morph.to_dict()
    if "Gender" in morph:
        g = morph["Gender"]
        if g == "Masc": return "masculin"
        if g == "Fem":  return "féminin"

    # From surrounding pronouns (il/elle, son/sa, lui/elle)
    start = max(0, token.i - 10)
    end   = min(len(doc), token.i + 10)
    masc_count = 0
    fem_count  = 0
    for t in doc[start:end]:
        lemma = t.lemma_.lower()
        if lemma in ["il", "lui", "son", "ses", "le"] and t.pos_ == "PRON":
            masc_count += 1
        elif lemma in ["elle", "sa", "ses", "la"] and t.pos_ == "PRON":
            fem_count += 1

    if masc_count > fem_count: return "masculin"
    if fem_count > masc_count: return "féminin"
    return "indéterminé"

# ── Syntactic role ──────────────────────────────────────────────────────────

def get_role(token):
    """Get the syntactic role of a token."""
    dep = token.dep_
    head_dep = token.head.dep_ if token.head != token else None

    # Handle conjunctions — look at head's head
    if dep == "conj":
        dep = head_dep

    if dep in ["nsubj", "ROOT", "obl:agent"]: return "Agent actif"
    elif dep == "nsubj:pass":                   return "Récepteur passif"
    elif dep == "nmod":                          return "Complément du nom"
    elif dep == "obj":                           return "Objet"
    else:                                        return "Autre"

# ── Main pipeline ───────────────────────────────────────────────────────────

def truncate_sentence(sent_text, max_len=MAX_SENT_LEN):
    if len(sent_text) <= max_len:
        return sent_text
    return sent_text[:max_len] + "..."

def is_false_positive(name):
    name_lower = name.lower().strip()
    if name_lower in FALSE_POSITIVES: return True
    if len(name_lower) <= 1: return True
    if name_lower.startswith("©"): return True
    if re.match(r'^\d+$', name_lower): return True
    return False

def process_novel(filepath):
    filename = os.path.basename(filepath)
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            text = f.read()[:MAX_CHARS]
    except Exception as e:
        return []

    # Skip very short files
    if len(text) < 1000:
        return []

    try:
        doc = nlp(text)
    except Exception:
        return []

    rows = []
    seen = set()

    for ent in doc.ents:
        if ent.label_ != "PER":
            continue

        name = ent.text.strip().replace("\n", " ")

        # Skip false positives
        if is_false_positive(name):
            continue

        # Get the main token (first content word of entity)
        main_token = None
        for token in ent:
            if token.pos_ in ["PROPN", "NOUN"]:
                main_token = token
                break
        if main_token is None:
            main_token = ent[0]

        # Get sentence context
        sent = main_token.sent
        sent_text = truncate_sentence(sent.text.strip())

        # Deduplicate same name in same sentence
        key = (filename, name, sent.start)
        if key in seen:
            continue
        seen.add(key)

        # Get syntactic role and gender
        role   = get_role(main_token)
        gender = detect_gender(main_token, doc)

        # Get head info
        head = (main_token.head.text, main_token.dep_)
        head_of_head = (main_token.head.head.text, main_token.head.dep_) if main_token.head != main_token else ("", "")

        rows.append({
            "fichier":             filename,
            "token_lexique":       name,
            "truncated_sentence":  sent_text,
            "lemme":               name,
            "genre":               gender,
            "tête":                str(head),
            "tête_de_tête":        str(head_of_head),
            "rôle":                role,
        })

    return rows

def main():
    start_time = time.time()
    corpus_files = sorted([
        os.path.join(CORPUS_DIR, f)
        for f in os.listdir(CORPUS_DIR)
        if f.endswith(".txt")
    ])

    print(f"Processing {len(corpus_files)} novels...")
    print(f"Output: {OUTPUT_FILE}")

    fieldnames = ["fichier", "token_lexique", "truncated_sentence", "lemme",
                  "genre", "tête", "tête_de_tête", "rôle"]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()

        total_rows = 0
        for i, filepath in enumerate(corpus_files, 1):
            fname = os.path.basename(filepath)
            rows = process_novel(filepath)
            if rows:
                writer.writerows(rows)
                f.flush()
                total_rows += len(rows)

            elapsed = time.time() - start_time
            eta = (elapsed / i) * (len(corpus_files) - i)
            print(f"  [{i:>3}/{len(corpus_files)}] {fname[:50]:<50} "
                  f"+{len(rows):>4} rows | total={total_rows:>7,} | ETA={eta/60:.0f}min")

    elapsed = time.time() - start_time
    print(f"\n✅ Done in {elapsed/60:.1f} minutes")
    print(f"   Total rows: {total_rows:,}")
    print(f"   Saved to:   {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
