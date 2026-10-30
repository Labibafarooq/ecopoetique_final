"""
Task 3 extension — multilingual human-name detection.

Adds English/Arabic-origin name detection on top of the existing French-only
spaCy pipeline (extract_humains.py), per Riccardo's explicit request in both
meeting transcripts — most recently: "we need to add Arabic names and
English names."

Design, addressing the two concerns Riccardo raised in the first meeting:

  1. Overfitting / false-positive risk ("there might be a name called bar in
     any other language"): every name found ONLY by the multilingual model
     (i.e. the French spaCy model missed it) must pass a MID-SENTENCE
     CAPITALIZATION check before being accepted. A word that is capitalized
     only because it happens to start a sentence is a weak signal — that's
     forced by position, not meaning. A word capitalized in the MIDDLE of a
     sentence, where nothing forces capitalization, is real evidence it's a
     proper noun. This directly implements Riccardo's own second proposal
     from the same meeting: "what I can do is I can search for names which
     are in the middle with the capital letter."

  2. Auditability: every row is tagged with a "source" column (fr_model vs
     multilingual_model), so the new, higher-risk detections can be
     reviewed or gold-set-checked separately from the already-trusted
     French ones — matching Labiba's own offer in the transcript ("if you
     want I can do a gold on that too... just checking if it's a real name
     or is it something else").

Model: Davlan/xlm-roberta-base-ner-hrl — XLM-RoBERTa fine-tuned for NER on
10 high-resource languages including Arabic and English. This is a genuine
multilingual model applied directly to the same French text (names of
Arab/English origin still appear in Latin script inside these French
novels — the task isn't detecting a different script, it's catching name
patterns the French-only model under-recognizes), matching what Riccardo
asked for ("a multi language model so it can detect all of the other
names"), not a separate per-language pipeline.

The French spaCy parse (dependency tree, morphology) is still the source of
truth for syntactic role and gender for EVERY name, including the new
multilingual-only ones — spaCy tokenizes/parses all text regardless of which
model found the entity, so a multilingual candidate's character span is
mapped back onto the already-parsed French doc via doc.char_span(), and the
exact same get_role()/detect_gender() logic from the original script is
reused unchanged.

Output: dépendants_HUMAINS_multilingual.csv — a SEPARATE file, does not
overwrite the original dépendants_HUMAINS.csv, so both remain available for
comparison.
"""

import os
import re
import csv
import sys
import time
import argparse
import spacy
from transformers import pipeline

CORPUS_DIR  = os.path.expanduser("~/ecopoetique/CORPUS_TOTAL")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/morphosyntaxe/dépendants_HUMAINS_multilingual.csv")
MAX_CHARS    = 100000  # same limit as the original script, for direct comparability
MAX_SENT_LEN = 150
NER_MODEL    = "Davlan/xlm-roberta-base-ner-hrl"
CHUNK_CHARS  = 1500     # conservative, keeps chunks well under XLM-R's 512 subtoken limit
ANIMAUX_LEXIQUE = os.path.expanduser("~/ecopoetique/lexiques/ANIMAUX.txt")
PLANTES_LEXIQUE = os.path.expanduser("~/ecopoetique/lexiques/PLANTES.txt")


def load_bio_lexicon():
    """
    Project-specific false-positive guard: this corpus is specifically about
    animal/plant representation, so a capitalized common noun for an animal
    or plant (e.g. 'Ours' = bear) is a real, likely source of false person-
    detections, not a hypothetical edge case. Load both lexicons so any
    multilingual-only candidate matching a known animal/plant term can be
    flagged/dropped rather than silently counted as a human character.
    """
    terms = set()
    for path in (ANIMAUX_LEXIQUE, PLANTES_LEXIQUE):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip().lower()
                    if line:
                        terms.add(line)
        except FileNotFoundError:
            pass
    return terms


BIO_LEXICON = load_bio_lexicon()

FALSE_POSITIVES = {
    "nord compo", "gallimard", "flammarion", "grasset", "seuil", "actes sud",
    "fayard", "albin michel", "stock", "minuit", "isbn", "p.", "dr",
}

nlp = spacy.load("fr_core_news_lg")


def load_ner_pipeline(device):
    return pipeline(
        "ner",
        model=NER_MODEL,
        aggregation_strategy="simple",
        device=device,  # -1 = CPU, 0 = first CUDA GPU
    )


# ── Gender detection (unchanged from extract_humains.py) ────────────────────

def detect_gender(token, doc):
    morph = token.morph.to_dict()
    if "Gender" in morph:
        g = morph["Gender"]
        if g == "Masc": return "masculin"
        if g == "Fem":  return "féminin"

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


# ── Syntactic role (unchanged from extract_humains.py) ───────────────────────

def get_role(token):
    dep = token.dep_
    head_dep = token.head.dep_ if token.head != token else None
    if dep == "conj":
        dep = head_dep
    if dep in ["nsubj", "ROOT", "obl:agent"]: return "Agent actif"
    elif dep == "nsubj:pass":                   return "Récepteur passif"
    elif dep == "nmod":                          return "Complément du nom"
    elif dep == "obj":                           return "Objet"
    else:                                        return "Autre"


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


# ── Multilingual NER pass ─────────────────────────────────────────────────────

def _merge_zero_gap(spans):
    merged = []
    for e in spans:
        if merged and e["start"] == merged[-1]["end"]:
            merged[-1]["end"] = e["end"]
        else:
            merged.append({"start": e["start"], "end": e["end"]})
    return merged


def run_multilingual_ner(doc, ner_pipe):
    """
    Chunk the novel by sentence boundaries (respecting CHUNK_CHARS), run the
    multilingual NER model per chunk, map every PERSON entity back onto
    absolute character offsets in the full doc. Also collects every ORG
    surface string the model tags anywhere in the novel (see org_names
    below) — used as a false-positive guard for band/group names that get
    inconsistently tagged PER vs ORG by the same model (e.g. "Nirvana"
    itself splits into ORG("Nir") + PER("vana") in this model — confirmed
    live, 2026-07-08).

    Returns: (per_results, org_names)
      per_results: list of (char_start, char_end, surface_text)
      org_names: set of lowercased ORG surface strings found anywhere
    """
    results = []
    org_names = set()
    sents = list(doc.sents)
    i = 0
    while i < len(sents):
        chunk_start_char = sents[i].start_char
        running_len = 0
        j = i
        while j < len(sents) and running_len + len(sents[j].text) <= CHUNK_CHARS:
            running_len += len(sents[j].text)
            j += 1
        j = max(j, i + 1)  # always include at least one sentence, even if it alone exceeds CHUNK_CHARS
        chunk_end_char = sents[j - 1].end_char
        chunk_text = doc.text[chunk_start_char:chunk_end_char]

        try:
            entities = ner_pipe(chunk_text)
        except Exception:
            entities = []

        # XLM-R's subword tokenizer sometimes splits a name into two spans
        # of the SAME type with zero gap between them (e.g. "Émile" ->
        # "É" + "mile", "Théodore" -> "Th" + "éodore") — aggregation_strategy
        # ="simple" doesn't always re-merge these. A real word boundary
        # always has at least a space/punctuation between separate names, so
        # merging any two consecutive same-type spans with EXACTLY zero
        # character gap is safe and fixes this without risking merging
        # genuinely distinct names.
        per_spans = [e for e in entities if "PER" in e.get("entity_group", "").upper()]
        org_spans = [e for e in entities if "ORG" in e.get("entity_group", "").upper()]

        for e in _merge_zero_gap(org_spans):
            start, end = _extend_to_word_boundary(chunk_text, e["start"], e["end"])
            org_names.add(chunk_text[start:end].lower())

        for e in _merge_zero_gap(per_spans):
            start, end = _extend_to_word_boundary(chunk_text, e["start"], e["end"])
            abs_start = chunk_start_char + start
            abs_end   = chunk_start_char + end
            surface   = chunk_text[start:end]
            results.append((abs_start, abs_end, surface))

        i = j

    return results, org_names


def is_known_org(name, org_names):
    words = name.lower().split()
    if name.lower() in org_names:
        return True
    return any(w in org_names for w in words)


def _extend_to_word_boundary(text, start, end):
    """
    Fixes truncation the zero-gap merge doesn't catch: cases where only ONE
    half of a split name got tagged PER at all (e.g. "Mauny" -> only "ny"
    tagged, "Lippmann" -> only "pmann" tagged — the model never labeled
    "Mau"/"Lip" as an entity, so there's no adjacent PER span to merge with).
    If the span starts or ends mid-word (the adjacent character is a letter,
    not whitespace/punctuation), extend outward to the nearest real word
    boundary — reconstructing the whole word regardless of how the model
    tagged its pieces.
    """
    while start > 0 and text[start - 1].isalpha():
        start -= 1
    while end < len(text) and text[end].isalpha():
        end += 1
    return start, end


def is_mid_sentence_capitalized(span):
    """
    Riccardo's false-positive guard: accept a multilingual-only candidate
    only if it appears capitalized somewhere that ISN'T the first token of
    its sentence — capitalization forced by sentence-initial position is a
    weak signal; capitalization in the middle of a sentence is a strong one.
    """
    first_token = span[0]
    is_sentence_initial = (first_token.i == span.sent[0].i)
    is_capitalized = first_token.text[:1].isupper()
    return is_capitalized and not is_sentence_initial


def _degender_variants(word):
    """
    Cheap French gender/number normalization for lexicon lookup, without a
    full morphological analyzer. Catches common patterns:
      ourse -> ours (strip feminine -e)
      chatte -> chat, lionne -> lion (strip -e then collapse doubled consonant)
      plural -s / -x already handled separately via spaCy's lemma.
    Not exhaustive (French has real irregulars: loup/louve), but covers the
    regular cases cheaply; irregulars still get a chance via the lemma check.
    """
    variants = {word}
    if word.endswith("e") and len(word) > 2:
        stripped = word[:-1]
        variants.add(stripped)
        if len(stripped) > 1 and stripped[-1] == stripped[-2]:
            variants.add(stripped[:-1])  # collapse doubled consonant
    return variants


def is_bio_lexicon_term(name, doc_for_lemma=None):
    """
    This corpus is specifically about animal/plant representation, so a
    capitalized common noun for an animal or plant (e.g. 'Ours' = bear) is a
    real, likely source of false person-detections, not a hypothetical edge
    case — found exactly this in initial testing (and its feminine form
    'Ourse' slipped through the first, exact-match-only version of this
    check). Checks the raw word, spaCy's lemma (catches plurals reliably),
    and cheap gender-variant stripping (catches ours/ourse, chat/chatte).
    """
    for w in name.lower().split():
        if w in BIO_LEXICON:
            return True
        if _degender_variants(w) & BIO_LEXICON:
            return True
    if doc_for_lemma is not None:
        lemmas = {t.lemma_.lower() for t in doc_for_lemma}
        if lemmas & BIO_LEXICON:
            return True
    return False


def get_loc_entities(doc):
    """
    Place-name guard: collect every LOC entity the French spaCy model already
    tags in this novel (no extra cost — same doc.ents pass used for PER).
    A multilingual-only PER candidate that matches a known LOC in the SAME
    novel (e.g. 'Sables' from 'Les Sables-d'Olonne') is far more likely a
    place reference than a human character.
    """
    locs = set()
    for ent in doc.ents:
        if ent.label_ == "LOC":
            locs.add(ent.text.strip().lower())
            for word in ent.text.strip().lower().split():
                locs.add(word)
    return locs


def is_known_location(name, loc_entities):
    words = name.lower().split()
    if name.lower() in loc_entities:
        return True
    return any(w in loc_entities for w in words)


def process_novel(filepath, ner_pipe):
    filename = os.path.basename(filepath)
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            text = f.read()[:MAX_CHARS]
    except Exception:
        return []

    if len(text) < 1000:
        return []

    try:
        doc = nlp(text)
    except Exception:
        return []

    rows = []
    seen = set()          # (name, sent_start) already emitted, from either model
    fr_names_lower = set()  # names already caught by the French model this novel

    # ── Pass 1: French model (exactly as in the original script) ──────────
    for ent in doc.ents:
        if ent.label_ != "PER":
            continue
        name = ent.text.strip().replace("\n", " ")
        if is_false_positive(name):
            continue

        main_token = next((t for t in ent if t.pos_ in ["PROPN", "NOUN"]), ent[0])
        sent = main_token.sent
        sent_text = truncate_sentence(sent.text.strip())

        key = (filename, name, sent.start)
        if key in seen:
            continue
        seen.add(key)
        fr_names_lower.add(name.lower())

        rows.append({
            "fichier": filename, "token_lexique": name, "truncated_sentence": sent_text,
            "lemme": name, "genre": detect_gender(main_token, doc),
            "tête": str((main_token.head.text, main_token.dep_)),
            "tête_de_tête": str((main_token.head.head.text, main_token.head.dep_)
                                if main_token.head != main_token else ("", "")),
            "rôle": get_role(main_token), "source": "fr_model",
        })

    # ── Pass 2: multilingual model, only for names the French model missed ──
    loc_entities = get_loc_entities(doc)
    ml_hits, org_names = run_multilingual_ner(doc, ner_pipe)
    for abs_start, abs_end, surface in ml_hits:
        name = surface.strip().replace("\n", " ")
        if is_false_positive(name) or name.lower() in fr_names_lower:
            continue

        span = doc.char_span(abs_start, abs_end, alignment_mode="expand")
        if span is None or len(span) == 0:
            continue

        if is_bio_lexicon_term(name, doc_for_lemma=span):
            continue  # a known animal/plant term (incl. gender/plural variants)

        if is_known_location(name, loc_entities):
            continue  # matches a place the French model already tagged as LOC

        if is_known_org(name, org_names):
            continue  # matches a band/group/organization tagged elsewhere (e.g. Nirvana, the Smiths)

        if not is_mid_sentence_capitalized(span):
            continue  # fails Riccardo's false-positive guard — drop it

        main_token = next((t for t in span if t.pos_ in ["PROPN", "NOUN"]), span[0])
        sent = main_token.sent
        sent_text = truncate_sentence(sent.text.strip())

        key = (filename, name, sent.start)
        if key in seen:
            continue
        seen.add(key)

        rows.append({
            "fichier": filename, "token_lexique": name, "truncated_sentence": sent_text,
            "lemme": name, "genre": detect_gender(main_token, doc),
            "tête": str((main_token.head.text, main_token.dep_)),
            "tête_de_tête": str((main_token.head.head.text, main_token.head.dep_)
                                if main_token.head != main_token else ("", "")),
            "rôle": get_role(main_token), "source": "multilingual_model",
        })

    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", type=int, default=0, help="process only the first N novels")
    ap.add_argument("--device", type=int, default=-1, help="-1=CPU, 0=first CUDA GPU")
    args = ap.parse_args()

    ner_pipe = load_ner_pipeline(args.device)

    start_time = time.time()
    corpus_files = sorted(
        os.path.join(CORPUS_DIR, f) for f in os.listdir(CORPUS_DIR) if f.endswith(".txt")
    )
    if args.test:
        corpus_files = corpus_files[:args.test]

    fieldnames = ["fichier", "token_lexique", "truncated_sentence", "lemme",
                  "genre", "tête", "tête_de_tête", "rôle", "source"]

    # 2026-10-20: resume support added — this script originally always opened
    # OUTPUT_FILE in "w" mode with no done-novel check, so restarting after
    # a pause (e.g. the 72/925-novel run paused since Oct 8) silently
    # reprocessed everything from novel 1, wasting ~4h of redundant CPU work
    # for no reason. Now skips any novel filename already present in the
    # existing output and appends instead of truncating.
    done_novels = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            csv.field_size_limit(10_000_000)
            done_novels = {r["fichier"] for r in csv.DictReader(f, delimiter="\t")}
    corpus_files = [fp for fp in corpus_files if os.path.basename(fp) not in done_novels]
    if done_novels:
        print(f"Resuming: {len(done_novels)} novels already done, skipping them")

    print(f"Processing {len(corpus_files)} novels (device={'CPU' if args.device < 0 else 'GPU'})...")
    print(f"Output: {OUTPUT_FILE}")

    write_header = not os.path.exists(OUTPUT_FILE) or not done_novels
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        if write_header:
            writer.writeheader()

        total_rows = 0
        total_fr = 0
        total_ml = 0
        for i, filepath in enumerate(corpus_files, 1):
            fname = os.path.basename(filepath)
            t0 = time.time()
            rows = process_novel(filepath, ner_pipe)
            el = time.time() - t0
            if rows:
                writer.writerows(rows)
                f.flush()
                total_rows += len(rows)
                total_fr += sum(1 for r in rows if r["source"] == "fr_model")
                total_ml += sum(1 for r in rows if r["source"] == "multilingual_model")

            elapsed = time.time() - start_time
            eta = (elapsed / i) * (len(corpus_files) - i)
            print(f"  [{i:>3}/{len(corpus_files)}] {fname[:45]:<45} "
                  f"+{len(rows):>4} rows ({el:.1f}s) | fr={total_fr:,} ml_new={total_ml:,} "
                  f"| ETA={eta/60:.0f}min", flush=True)

    elapsed = time.time() - start_time
    print(f"\nDone in {elapsed/60:.1f} minutes")
    print(f"  Total rows: {total_rows:,}  (fr_model={total_fr:,}, multilingual_model={total_ml:,})")
    print(f"  Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
