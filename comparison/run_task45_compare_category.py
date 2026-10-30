"""
Task 4.5 — Compare-target Classification
Classifies what each figurative animal/plant mention is being compared TO,
into one of 6 categories defined by Riccardo Barontini (2026-07-08, see
métaphore/"Catégories analyse comparés.docx"):

  O  : Objets et structures artificiels (man-made objects/technological artifacts)
  NH : Créatures non humaines vivantes et processus biologiques (animals, plants,
       biological processes in non-human living things)
  E  : Éléments naturels inanimés et processus naturels (landscapes, geological
       formations, weather, non-living natural world)
  CH : Corps humain et processus biologiques (human body, physiological
       functions, biological processes)
  A  : Concepts abstraits (politics, religion, art, social institutions)
  P  : États psychologiques et fonctions cognitives (emotions, sensations,
       memory, imagination)

Ollama call config mirrors Task 1's proven-working pattern (thinking ON,
no format:json constraint, large num_predict) — Task 2's script originally
used num_predict=200 with no thinking control, which silently returned 0
successes because qwen3 exhausted the budget mid-thought before ever
emitting JSON; fixed 2026-07-08 in run_task2_subcategories.py and mirrored
here from the start.

Input:  comparison/gold_task2_task45_RB.csv (for validation against Riccardo's
        actual annotations) — full-corpus input file not yet built.
Output: comparison/resultats_task45_compare_category.csv

Handling of gold-set special values (per Riccardo's email, 2026-07-08):
  - 'X'/'x' rows: wrongly classified as figurative by Task 1 in the first
    place — skip entirely (not applicable, not scored).
  - Blank categorie_compare on IMAG/LOC_IDIOM/COUL/META_VERB-type rows:
    legitimate "not applicable" (e.g. IMAG has no compare-target) — skip,
    do not treat as missing.
  - '?' rows: excluded from scoring per Riccardo (tentative — confirm final
    convention with him).
"""

import os, csv, re, json, time, requests
from collections import Counter

OLLAMA_URL  = "http://127.0.0.1:11449/api/chat"
MODEL       = "qwen3:30b"
GOLD_FILE   = os.path.expanduser("~/ecopoetique/métaphore/gold_task2_task45_CURRENT.csv")  # repointed 2026-10-13: old RB file is stale/pre-schema-fix; see métaphore/run_task2_subcategories.py header for the decoy-blank-template warning (same gold file, same decoy exists for this task too)
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/comparison/resultats_task45_compare_category.csv")
TIMEOUT     = 300

CATEGORIES = {
    "CH": ("Corps humain et processus biologiques",
           "références métaphoriques au corps humain, fonctions physiologiques, processus biologiques humains"),
    "P":  ("États psychologiques et fonctions cognitives",
           "émotions, sensations, fonctions cognitives comme la mémoire et l'imagination"),
    "NH": ("Créatures non humaines vivantes et processus biologiques",
           "animaux, plantes, processus biologiques chez les êtres vivants non humains"),
    "O":  ("Objets et structures artificiels",
           "objets fabriqués par l'homme, artefacts technologiques"),
    "E":  ("Éléments naturels inanimés et processus naturels",
           "paysages naturels, formations géologiques, phénomènes météorologiques, aspects non vivants du monde naturel"),
    "A":  ("Concepts abstraits",
           "idées abstraites : politique, religion, art, institutions sociales comme le mariage"),
}
VALID_CODES = list(CATEGORIES.keys())

# ── LLM PROMPT — Conceptual Metaphor Theory (CMT) step-by-step chain ────────
# Redesigned 2026-07-08 per literature on CMT-based prompting for metaphor
# interpretation (arxiv 2502.01901: sequential source->target->differ questions
# reached F1 up to 82.59, vs. asking for the answer directly) and tenor-
# vehicle-ground extraction (arxiv 2010.05633: validate via the shared
# "ground" property before committing to a classification). Our first prompt
# fix (tenor/vehicle warning) helped (Task 4.5 gold accuracy 30%->63.5%) but
# residual CH<->NH confusion remained — this forces the model through each
# step explicitly instead of just warning it not to make the mistake.
#
# Corrected 2026-07-10 per Riccardo's email: the categories classify what
# KIND OF ENTITY the cible (target/comparé) literally IS, never the semantic
# domain of the trait/quality the comparison illustrates. An earlier version
# of this prompt told the model "personality trait -> P, not CH" and "voice/
# artistic quality -> A, not CH" — both wrong, since a personality trait
# attributed to a human referent is still CH (the referent is a person), a
# voice attributed to a human referent is still CH, etc. Riccardo's own
# example: "Je bats lâchement en retraite... comme un rat" -> cible = "il"
# (a person) -> CH, even though the illustrated trait (lâcheté) is
# psychological. Contrast: "Mes émotions se cachaient comme des rats" ->
# cible = "mes émotions" -> P. "L'île ressemblait à un rat" -> cible =
# "l'île" -> E. Same vehicle, different category, purely by what the cible
# itself is.
def make_prompt(token, context, subcategory):
    cats_desc = "\n".join(f"  {code}: {info[0]} — {info[1]}" for code, info in CATEGORIES.items())
    return f"""Tu es expert en stylistique française et en figures de style, formé à
la théorie de la métaphore conceptuelle (véhicule / cible / fondement commun).

Le mot «{token}» est utilisé de façon FIGURATIVE dans ce contexte :
«{context}»

Cette figure appartient à la catégorie structurelle: {subcategory}

Réponds aux questions suivantes DANS L'ORDRE, en JSON, une par une :

1. vehicule : que désigne «{token}» littéralement, en dehors de ce contexte
   (ex: "rat" = un petit rongeur) ? Réponse brève.
2. cible : dans CETTE phrase précise, quel est le RÉFÉRENT RÉEL — la vraie
   personne, chose, créature ou idée — auquel «{token}» est comparé ? C'est
   en général le sujet réel de la comparaison (ex: "il", "elle", "mes
   émotions", "l'île", "le mariage"). Réponse brève, un groupe nominal.
3. fondement_commun : quelle qualité ou propriété partagée justifie cette
   comparaison entre le véhicule et la cible (ex: pingrerie, ruse, fragilité) ?
   Réponse brève. Cette qualité NE SERT PAS à choisir la catégorie (étape 5) —
   elle est juste là pour vérifier que la comparaison est cohérente.
4. verification : le véhicule (réponse 1) et la cible (réponse 2) sont-ils
   des choses DIFFÉRENTES ? (yes/no — si non, ce n'est probablement pas une
   vraie figure, mais classe quand même du mieux possible)
5. code : classe la CIBLE (réponse 2) selon LE TYPE D'ENTITÉ QU'ELLE EST
   LITTÉRALEMENT — jamais selon le domaine de la qualité/du trait illustré
   (réponse 3). Choisis parmi :

{cats_desc}

EXEMPLES DE RÉFÉRENCE (inventés, un par catégorie — même s'ils ne parlent pas
de «{token}», la LOGIQUE de classement est ce qui compte) :
- CH : «Pierre courait comme un lièvre, le souffle court» — cible = «Pierre»
  (une personne, même si le trait "vitesse/souffle" a une composante
  physique OU comportementale) → CH.
- P : «Sa jalousie rôdait comme un loup affamé» — cible = «sa jalousie» (une
  émotion elle-même, sujette grammaticale de l'action) → P.
- NH : «Le chat de la voisine grimpait comme un écureuil» — cible = «le
  chat» (un animal non-humain, pas une personne) → NH.
- O : «La vieille voiture toussait comme un vieillard essoufflé» — cible =
  «la voiture» (un objet fabriqué) → O.
- E : «La falaise se dressait comme une sentinelle» — cible = «la falaise»
  (un élément naturel non-vivant) → E.
- A : «Le mariage, cette cage dorée, l'étouffait» — cible = «le mariage»
  (une institution/pratique sociale, pas une personne précise) → A.

⚠ RÈGLE CENTRALE : la catégorie dépend uniquement de ce que la cible EST, pas
de ce que la comparaison dit d'elle. Un trait de caractère, une émotion, une
compétence, un défaut — n'importe quelle qualité — peut être attribué à
n'importe quel type d'entité. La qualité ne change JAMAIS la catégorie.
Ignore complètement le sens du fondement_commun (réponse 3) pour choisir le
code ; utilise uniquement la nature de la cible (réponse 2).

Procédure : identifie d'abord QUI ou QUOI est réellement comparé au véhicule
(la cible, réponse 2), puis classe cette entité :
- si c'est une personne (ou une partie/fonction physique de son corps) → CH
- si c'est un état psychologique, une émotion, une sensation, une faculté
  cognitive (mémoire, imagination...) en tant que TEL (ex: "mes émotions",
  "son esprit", "sa mémoire") → P
- si c'est un animal, une plante, ou un processus biologique non-humain → NH
- si c'est un objet fabriqué, une structure artificielle → O
- si c'est un élément naturel non-vivant (paysage, mer, ciel, météo,
  formation géologique...) → E
- si c'est une idée, une institution, une pratique sociale/culturelle
  (politique, religion, art, mariage, justice...) → A

Exemples (d'après Riccardo Barontini, 2026-07-10) — même véhicule ("rat"),
catégorie différente selon la cible :
- «Je bats lâchement en retraite... comme un rat» : cible = « il » (une
  personne). Le trait illustré (lâcheté) est psychologique, MAIS la cible
  est une personne → CH, PAS P. Ne classe jamais par le domaine du trait.
- «Mes émotions se cachaient comme des rats» : cible = « mes émotions »
  (un état psychologique lui-même, pas une personne) → P.
- «L'île ressemblait à un rat» : cible = « l'île » (un élément naturel) → E.

⚠ Attention à la voix/au chant : la cible n'est PAS automatiquement la
personne qui parle/chante. Regarde ce que la phrase compare RÉELLEMENT :
- «une voix d'aéroport... annonça» : c'est LA VOIX elle-même qui agit/est
  décrite comme sujet, pas la personne → cible = « la voix » → A (qualité
  artistique/esthétique du son), PAS CH.
- «il chantait comme un rossignol» : ici c'est LA PERSONNE qui est le sujet
  de l'action de chanter, le véhicule décrit COMMENT ELLE chante → cible =
  « il » (la personne) → CH.
Distingue : si le nom (voix/chant/voice) est lui-même le sujet grammatical
de la phrase ou l'objet direct de la comparaison → cible = ce nom → A. Si
c'est la PERSONNE qui est le sujet et que voix/chant n'est qu'un détail
descriptif → cible = la personne → CH.

⚠ Expressions figées, comparaisons rhétoriques, et descriptions poétiques
détournées — ne prends PAS le nom le plus proche du véhicule au pied de la
lettre si la phrase ne parle pas vraiment de cette chose littérale :
- Locution figée sans référent littéral (ex: "ménager la chèvre et le
  chou" = essayer de contenter tout le monde) : il n'y a PAS de chèvre ou
  de chou réels dans la scène. La cible est le COMPORTEMENT/CONCEPT abstrait
  nommé par l'expression (ici : l'indécision, le compromis) → A.
- Énumération rhétorique de paires incompatibles (ex: "différents comme
  mouton et carpe, tambour et flûte") : la cible n'est ni le mouton ni la
  carpe — c'est la NOTION ABSTRAITE d'incompatibilité/différence que
  l'énumération illustre → A.
- Description poétique/violente détournée (ex: "un livre se fraye un
  chemin de loup dans votre gorge") : ne classe pas "chemin" comme un lieu
  physique (E) si la phrase décrit en réalité une sensation, une expérience
  de lecture, ou un effet ressenti — cherche ce que la phrase décrit
  VRAIMENT en train de se passer, pas le sens littéral du nom isolé.
- Si le véhicule est utilisé pour décrire l'apparence fantastique/grotesque
  d'un PERSONNAGE humain (ex: "un être composite avec une truffe de
  chien..." décrivant quelqu'un) → cible = ce personnage → CH, même si la
  description elle-même ressemble à une créature non-humaine.
Dans tous ces cas : identifie d'abord de QUOI la phrase parle VRAIMENT
(quel comportement, quelle notion, quel personnage) avant de choisir la
catégorie — ne t'arrête pas au nom syntaxiquement le plus proche du
véhicule si ce n'est pas le vrai sujet de la comparaison.

Réponds UNIQUEMENT avec ce JSON :
{{"vehicule": "...", "cible": "...", "fondement_commun": "...", "verification": "yes/no", "code": "CODE"}}"""

# ── RULE-BASED IDIOM PRE-FILTER — found 2026-10-15 from real test-set errors:
# a handful of fixed French idioms/slang using plant or animal vehicles have
# a non-literal target the model doesn't reliably infer from world knowledge
# alone. Isolated, high-precision substring match, checked BEFORE the LLM
# call — mirrors Task 2's idiom-lexicon architecture precisely so a wrong
# entry here can't ripple into unrelated rows the way a shared-prompt edit
# would (confirmed twice today, Task 2 and Task 4.5, that prompt-text edits
# cause unrelated regressions).
IDIOM_TARGET_OVERRIDES = [
    # (token lemma, required phrase(s) ALL must appear nearby, target code)
    ("prune", ["pren", "une prune"], "A"),   # "(se) prendre une prune" = get a fine/ticket — "pren" covers prend/prends/prenez/prenons/prennent; bare "une prune" alone also matches literal fruit descriptions (verified against real corpus: "une prune de Cythère" comparing fruit tastes)
    ("figue", ["mi-figue mi-raisin"], "A"),    # fixed idiom: mixed feelings
    ("raisin", ["mi-figue mi-raisin"], "A"),
    ("navet", ["navet"], "A"),                 # slang: a bad film/work (figurative-only input, so the literal-vegetable reading is already excluded upstream by Task 1)
    ("pomme", ["discorde"], "A"),  # "pomme de discorde" = source of conflict (abstract)
    # Rejected after checking real corpus samples (2026-10-15): "pépin" (all
    # real occurrences are literal seeds, not the "avoir un pépin" idiom) and
    # "asperge" (raw substring match was catching the unrelated word
    # "s'asperger" — same false-positive trap as "grimace" vs "grimé" found
    # earlier for Task 2).
]

def rule_based_target_override(token, context):
    ctx = context.lower()
    for tok_lemma, phrases, code in IDIOM_TARGET_OVERRIDES:
        if tok_lemma == token.lower() and all(p in ctx for p in phrases):
            return code
    return None

# ── OLLAMA CALL (mirrors Task 1's proven config: thinking ON, no format constraint,
#    large num_predict — NOT Task 2's original broken num_predict=200) ──────────
def call_ollama(prompt, _retries=1):
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0, "num_predict": 8000, "num_ctx": 16384},
        }, timeout=TIMEOUT)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        m = re.search(r'\{.*?\}', content, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            code = data.get("code", "").strip().upper()
            raison = (f"véhicule={data.get('vehicule','')} | cible={data.get('cible','')} | "
                      f"fondement={data.get('fondement_commun','')} | diff={data.get('verification','')}")
            if code in VALID_CODES:
                return code, raison
        for code in VALID_CODES:
            if code in content:
                return code, ""
        return "UNKNOWN", content[:100]
    except requests.exceptions.Timeout:
        # found 2026-10-15: timeouts are transient GPU-contention artifacts,
        # not real classification failures (3/78 dev rows, 2/76 test rows
        # were pure timeouts) — one retry recovers these for free.
        if _retries > 0:
            return call_ollama(prompt, _retries=_retries - 1)
        return "ERROR", "timeout after retry"
    except Exception as e:
        return "ERROR", str(e)[:80]

def is_x(v):
    return v.strip().lower() == "x"

def load_gold_rows(path):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    return rows

def main():
    rows = load_gold_rows(GOLD_FILE)
    print(f"Total gold rows: {len(rows)}")

    usable = []
    for r in rows:
        if is_x(r.get("subcategorie_metaphore", "")) or is_x(r.get("categorie_compare", "")) or is_x(r.get("notes", "")):
            continue  # wrongly classified as figurative — skip per Riccardo
        gold_cmp = r.get("categorie_compare", "").strip()
        if gold_cmp == "?":
            continue  # excluded per Riccardo, pending final confirmation
        if not gold_cmp:
            continue  # legitimate N/A (e.g. IMAG) or genuinely unexplained (e.g. id 56) — skip either way, not a target for classification validation
        usable.append(r)

    print(f"Usable rows (real categorie_compare label, not X/blank/?): {len(usable)}")

    fields = ["id", "fichier", "token_lexique", "contexte", "subcategorie_metaphore",
              "gold_categorie_compare", "predicted_categorie_compare", "raison", "correct"]

    # Resume support: skip ids already present in OUTPUT_FILE instead of
    # overwriting (this script previously opened in "w" mode unconditionally,
    # which silently discarded progress on any restart — found 2026-07-08
    # after a run was interrupted mid-way).
    done_ids = set()
    correct_done = 0
    write_header = True
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
        done_ids = {r["id"] for r in existing}
        correct_done = sum(1 for r in existing if r.get("correct", "").strip() == "True")
        write_header = len(existing) == 0
        if done_ids:
            print(f"Resuming: {len(done_ids)} rows already done ({correct_done} correct)")

    usable = [r for r in usable if r.get("id", "") not in done_ids]
    print(f"Remaining to classify: {len(usable)}")

    out_f = open(OUTPUT_FILE, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=fields)
    if write_header:
        writer.writeheader()

    correct = correct_done  # carries forward already-scored rows from a resumed run
    total_scored_base = len(done_ids)
    start = time.time()
    for i, r in enumerate(usable, 1):
        token = r["token_lexique"].strip()
        ctx = r["contexte"].strip()
        subcat = r.get("subcategorie_metaphore", "").strip()
        gold = r["categorie_compare"].strip().upper()

        code, raison = call_ollama(make_prompt(token, ctx, subcat))
        ok = (code == gold)
        correct += ok

        writer.writerow({
            "id": r.get("id", ""), "fichier": r.get("fichier", ""),
            "token_lexique": token, "contexte": ctx,
            "subcategorie_metaphore": subcat,
            "gold_categorie_compare": gold,
            "predicted_categorie_compare": code,
            "raison": raison, "correct": ok,
        })
        out_f.flush()

        if i % 10 == 0 or i == len(usable):
            elapsed = time.time() - start
            seen = total_scored_base + i
            print(f"  [{i}/{len(usable)} this run, {seen} total] correct={correct} ({correct/seen*100:.1f}%) elapsed={elapsed/60:.1f}min")

    out_f.close()
    total = total_scored_base + len(usable)
    print(f"\nFinal: {correct}/{total} = {correct/total*100:.1f}%")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
