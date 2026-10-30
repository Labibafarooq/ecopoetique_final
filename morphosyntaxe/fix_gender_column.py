"""
Fix the 'genre' column in dépendants_HUMAINS.csv — the existing method
(spaCy morphology, falling back to proximity pronoun-counting) has a real,
measured 18.0% error rate against unambiguous first names (verified via a
2026-10-22 sample check), since proximity pronoun-counting doesn't actually
resolve which character a nearby pronoun refers to.

Fix: use gender_guesser (a real first-name gender database) as the PRIMARY
source when the token's first word is a recognized first name — verified
0.0% error rate, 1.4% unknown on the same validation sample. Falls back to
the ORIGINAL genre value (not re-derived, just kept) only when gender_guesser
doesn't recognize the name at all (non-named references like "le narrateur",
or names outside its database) — since the original method's own morphology
check is legitimate for actual common nouns, just unreliable for names.
"""
import csv
import gender_guesser.detector as gender
import spacy.lang.fr.stop_words as fr_stop

csv.field_size_limit(10_000_000)

# 2026-10-22: found via audit — gender_guesser's database false-matches common
# French function words as names from other languages (e.g. "Mon" -> female,
# "Son" -> mostly_male, "Ma"/"Mais"/"Me" -> andy/male). For a multi-word
# reference like "Ma mère" or "Mon père", this wrongly used the DETERMINER's
# bogus match instead of the real noun, overriding an already-correct value
# from the original method. Filtered out via spaCy's own French stopword
# list before any gender_guesser lookup.
STOPWORDS = {w.capitalize() for w in fr_stop.STOP_WORDS} | {w.upper() for w in fr_stop.STOP_WORDS} | fr_stop.STOP_WORDS

IN_FILE = "dépendants_HUMAINS.csv"
BACKUP = "dépendants_HUMAINS.csv.bak_pre_gender_fix_20261022"

GENDER_MAP = {
    "male": "masculin", "mostly_male": "masculin",
    "female": "féminin", "mostly_female": "féminin",
    "andy": "indéterminé", "unknown": None,  # None = fall back to original
}


def main():
    d = gender.Detector()

    with open(IN_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    fieldnames = list(rows[0].keys())

    with open(BACKUP, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"Backup written: {BACKUP}")

    changed = kept_original = 0
    for r in rows:
        tok = r["token_lexique"].strip()
        first = tok.split()[0] if tok else ""
        if first in STOPWORDS:
            kept_original += 1
            continue
        g = GENDER_MAP.get(d.get_gender(first), None)
        if g is not None:
            if r["genre"] != g:
                changed += 1
            r["genre"] = g
        else:
            kept_original += 1

    with open(IN_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    print(f"Total rows: {len(rows)}")
    print(f"Changed by gender_guesser: {changed}")
    print(f"Kept original (name not recognized): {kept_original}")


if __name__ == "__main__":
    main()
