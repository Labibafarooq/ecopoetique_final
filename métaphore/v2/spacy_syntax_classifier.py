import sys, os
import spacy

sys.path.insert(0, os.path.dirname(__file__))
import run_task2_subcategories as _t2

nlp = spacy.load("fr_dep_news_trf")

COPULA_LEMMAS = {"être", "devenir", "redevenir"}
HEDGE_NOUNS = {"forme", "aspect", "sorte", "genre", "espèce", "allure", "air", "type", "façon"}
DEGREE_ADVERBS = {"moins", "plus", "aussi", "autant", "tant", "si"}
STATE_PARTICIPLES = {"poser", "asseoir", "coucher", "allonger", "suspendre",
                      "accrocher", "planter", "nicher", "percher", "étendre"}
NAMING_VERBS = {"surnommer", "appeler", "traiter", "traire", "qualifier", "désigner"}
DISGUISE_VERBS = {"déguiser", "habiller", "costumer", "transformer"}
DECORATE_VERBS = {"parsemer", "orner", "décorer", "broder", "tapisser"}
# 2026-10-20: subjective perception/description verbs governing "comme X" —
# the speaker's own characterization/judgment of someone, not a narrator's
# bare structural comparison, which is why Riccardo's gold treats these as
# MOD_ANALOG (the SUBCATEGORIES dict's own "analogie modalisée" examples
# already cover sembler/on dirait/avoir l'air de/ressembler à — this is the
# same family, just via a perception-reporting verb instead of a hedge
# phrase). Found via a real gold row: "Rachida l'a décrite comme une
# vipère" — gold=MOD_ANALOG, but the generic "comme" branch below was
# firing COMP_SIM on it since nothing here excludes this verb class.
PERCEPTION_VERBS = {"décrire", "considérer", "percevoir", "voir", "juger", "trouver"}

def find_token(doc, token):
    """Find the doc token matching our target lexical token (first match by lemma or text)."""
    tok_low = token.lower()
    for t in doc:
        if t.text.lower() == tok_low or t.lemma_.lower() == tok_low:
            return t
    # fallback: partial match on first few chars (handles inflected forms)
    for t in doc:
        if t.text.lower().startswith(tok_low[:4]) and t.pos_ in ("NOUN", "PROPN"):
            return t
    return None

def local_chain(tok, max_hops=1):
    """Token plus up to max_hops ancestors, stopping at clause boundaries
    (VERB/ADJ heads reached via obl/advcl/acl-type relations) so structure
    from unrelated parts of a long sentence never leaks in. All confirmed
    real cases (copula-identity, apposition) were within 1 hop; anything
    further up belongs to a different local phrase."""
    chain = [tok]
    cur = tok
    for _ in range(max_hops):
        nxt = cur.head
        if nxt == cur:
            break
        chain.append(nxt)
        cur = nxt
    return chain

def classify_syntax(token, context):
    """Returns one of META_NOM, META_APP, COMP_SIM, COMP_P, or None (no confident syntactic signal)."""
    # 0. Idiom-lexicon check — highest priority, before ANY syntactic branch.
    # 2026-10-20: found via real gold-error analysis that the "comme"
    # comparison branch (step 3 below) was overriding known frozen idioms
    # ("frais comme un gardon" -> COMP_SIM instead of LOC_IDIOM) because
    # nothing in this classifier checked the idiom lexicon before concluding
    # a live structural comparison. A known idiom is never a live
    # comparison, regardless of what syntax says, so it must win first.
    # Reuses run_task2_subcategories.py's own window-scoped lexicon check
    # (already fixed there today for the same whole-paragraph false-fire
    # risk) rather than a second, divergent copy.
    if _t2.rule_based_classify(token, context) == "LOC_IDIOM":
        return "LOC_IDIOM", "known idiom lexicon match"

    doc = nlp(context)
    tok = find_token(doc, token)
    if tok is None:
        return None, "token not found in parse"

    chain = local_chain(tok, max_hops=1)

    # 1. Copula identity check (highest priority, per the "il est le cerf de ma vie" rule)
    for node in chain:
        if node.lemma_ in HEDGE_NOUNS:
            continue  # "en forme de X" / "une sorte de X" is resemblance, not identity
        if any(c.lemma_ == "comme" for c in node.children):
            continue  # "était COMME X" is a hedged comparison, not "était X" identity
        if node.lemma_ in DEGREE_ADVERBS:
            continue  # "je suis MOINS QUE X" is a degree comparison (COMP_Q), not "je suis X" identity
        cop_children = [c for c in node.children if c.dep_ == "cop"]
        if cop_children and cop_children[0].lemma_ in COPULA_LEMMAS:
            has_subj = any(c.dep_.startswith("nsubj") for c in node.children) or \
                       any(c.dep_.startswith("nsubj") for c in node.head.children if node.head != node)
            if has_subj:
                # exclude conditional/hypothetical mood crudely via morph
                morph = cop_children[0].morph.get("Mood")
                if morph and "Cnd" in morph:
                    continue
                return "META_NOM", f"copula '{cop_children[0].text}' on '{node.text}' with subject"

    # 1b. Naming-verb check (surnommer/appeler/traiter de X) — same priority
    # as copula identity, since "on le traite de rat" IS an identity-naming
    # claim even without a copula. Found 2026-10-14: these made up a large
    # share of META_NOM rows spaCy's copula-only rule was missing entirely.
    for node in chain:
        head = node.head
        if head.lemma_ in NAMING_VERBS and node.dep_ in ("xcomp", "obl:arg", "obj"):
            has_subj = any(c.dep_.startswith("nsubj") for c in head.children)
            if has_subj:
                return "META_NOM", f"naming verb '{head.text}' with '{node.text}' as complement"

    # 1c. Exclamative-insult naming ("Quel têtard de quelle mare !") — token
    # itself bears an exclamative determiner "quel/quelle", functioning as
    # an implicit naming/characterization, similar to "quel idiot !"
    if any(c.lemma_ == "quel" and c.dep_ == "det" for c in tok.children):
        return "META_NOM", f"exclamative 'quel' determiner directly on '{tok.text}'"

    # 1d. IMAG: disguise ("déguisé en X") and decorative-pattern ("parsemé
    # de X") verbs — token is the complement of a verb describing how
    # something is dressed up as, or decorated with, the vivant, rather
    # than being the vivant itself.
    for node in chain:
        head = node.head
        if head.lemma_ in DISGUISE_VERBS or head.lemma_ in DECORATE_VERBS:
            return "IMAG", f"{'disguise' if head.lemma_ in DISGUISE_VERBS else 'decorative'} verb '{head.text}' governing '{node.text}'"

    # 2. Apposition check — DISABLED 2026-10-14: on the full dev set this
    # rule hit 1 correct (id=13) vs 4 wrong (gold was actually LOC_IDIOM or
    # IMAG — a frozen idiom or cultural-reference reading, which syntax
    # alone can't distinguish from genuine apposition). The LLM got 3/4 of
    # those right when tested directly, net +2 vs keeping this rule. Left
    # here commented for reference rather than deleted.
    # for node in chain:
    #     if node.dep_ == "appos":
    #         return "META_APP", f"'{node.text}' is appos of '{node.head.text}'"

    # 2b. Subjective perception/description verb governing "comme X"
    # (décrire/considérer/voir/juger... + comme + token) -> MOD_ANALOG, not
    # a bare structural comparison. Checked before step 3 since it's the
    # same "comme" surface form but a different, more specific structure
    # (someone's reported characterization of a third party) that step 3's
    # generic rule can't distinguish on its own — same priority logic as
    # the naming-verb check in 1b.
    for node in chain:
        head = node.head
        if head.lemma_ in PERCEPTION_VERBS and any(c.lemma_ == "comme" for c in node.children):
            return "MOD_ANALOG", f"perception verb '{head.text}' with 'comme {node.text}'"

    # 3. "comme" comparison: static vs process — only if "comme" directly
    # governs the token or the token's own immediate head (local to the
    # token's own phrase, not a comme elsewhere in a long sentence)
    for anchor in chain:
        comme_children = [c for c in anchor.children if c.lemma_ == "comme"]
        if not comme_children and anchor.head.lemma_ == "comme":
            comme_children = [anchor.head]
        if comme_children:
            if anchor.pos_ == "VERB":
                return "COMP_P", f"comme attaches to clausal verb '{anchor.text}'"
            # proximity constraint: in very long/run-on sentences, a totally
            # unrelated later clause can get syntactically dumped onto the
            # sentence ROOT as acl/acl:relcl just because it has nowhere
            # closer to attach (e.g. "vautours...45 words later...déclenchant").
            # A genuine participial modifier ("araignée fouettée") sits right
            # next to its noun, so require closeness in raw token position.
            has_clausal_mod = any(c.dep_ in ("acl", "acl:relcl") and abs(c.i - anchor.i) <= 4
                                   and c.lemma_ not in STATE_PARTICIPLES
                                   for c in anchor.children)
            if has_clausal_mod:
                return "COMP_P", f"compared NP '{anchor.text}' has clausal modifier"
            return "COMP_SIM", f"compared NP '{anchor.text}' is bare, no process"

    return None, "no confident syntactic signal"


if __name__ == "__main__":
    import csv, json
    with open("task2_dev_test_split.json") as f:
        split = json.load(f)
    dev_ids = set(split["dev_ids"])

    with open("gold_task2_task45_CURRENT.csv", encoding="utf-8") as f:
        gold = list(csv.DictReader(f, delimiter=";"))
    for r in gold:
        if r["subcategorie_metaphore"].strip().upper() == "META_ATT":
            r["subcategorie_metaphore"] = "META_NOM"

    TARGET_CATS = {"META_NOM", "META_APP", "COMP_SIM", "COMP_P"}
    dev_rows = [r for r in gold if r["id"] in dev_ids and r["subcategorie_metaphore"].strip() in TARGET_CATS]
    print(f"Dev rows in target categories: {len(dev_rows)}\n")

    correct = 0
    attempted = 0
    for r in dev_rows:
        token = r["token_lexique"].strip()
        ctx = r["contexte"].strip()
        gold_cat = r["subcategorie_metaphore"].strip()
        pred, reason = classify_syntax(token, ctx)
        if pred is not None:
            attempted += 1
            ok = pred == gold_cat
            correct += ok
            mark = "OK " if ok else "BAD"
            print(f"[{mark}] id={r['id']} tok={token} gold={gold_cat} pred={pred} | {reason}")
        else:
            print(f"[SKIP] id={r['id']} tok={token} gold={gold_cat} | {reason}")

    print(f"\nAttempted: {attempted}/{len(dev_rows)}")
    if attempted:
        print(f"Correct among attempted: {correct}/{attempted} = {correct/attempted*100:.1f}%")
