"""
Task 2 — Figurative Subcategory Classification
Classifies each figurative case into one of 12 subcategories, per Riccardo's
current, verified-current schema as of 2026-10-13:
  - schema_analogies_vivant_complet130726.csv (2026-07-13 reply): simplified
    the original 19 categories down to 11 — META_ATTR renamed META_NOM;
    COMME_SN/COMME_P/COMP_DEG renamed COMP_SIM/COMP_P/COMP_Q; META_VERB
    broadened into META_PRED (verb OR adjective); the five old "de+nature
    term" categories (DE_PARANGON/DE_MATIERE/DE_UNIVERS/DE_QUANTIF/DE_PROP)
    collapsed into just META_DET (token is N1, the metaphorizing term, e.g.
    "une forêt de pylônes") vs META_QUAL (token is N2, the metaphorizing
    term, e.g. "une mémoire d'éléphant") — a clean positional test, replacing
    the old semantic-domain test that caused the DE_PARANGON/DE_PROP
    confusion; COMME_SI/ANALOG_COMPLEX/META_FILEE dropped with no
    replacement (no longer valid output codes at all).
  - Riccardo's 2026-09-17 reply: MOD_ANALOG (dropped in the Jul13 pass)
    restored — "it seems that I have used MOD_ANALOG in the gold but
    eliminated it from the schema. So I guess we should put it back." No
    file was ever resent for this — it's a verbal amendment on top of the
    Jul13 file, combined here manually.
  - META_JUXT (eliminated 2026-07-10, folded into META_APP) predates both of
    the above and remains folded into META_APP, unaffected by the later
    changes.
Verified 2026-10-13 directly against `gold_task2_task45_CURRENT.csv` (the
real annotated gold file Riccardo returned 2026-07-13 — a `gold_task2_task45_FINAL.csv`
sitting in this same directory is a decoy, a never-annotated blank template
from before his reply came back; don't confuse the two). The gold file uses
`META_ATT` as shorthand for `META_NOM` in 28 of 29 rows for that category —
normalized in validate_task2_gold.py, not here.

Prompt restructured 2026-07-08 as a sequential DECISION TREE (mirroring how a
linguist would actually parse the sentence) instead of a flat 19-way pick —
same technique that fixed Task 0's RÉGIME NARRATIF, and matches literature on
LLM-assisted rule-script/decision-procedure prompting for figurative-language
classification (see MIPVU rule-script generation, arxiv 2603.10784). Gold-set
validation (2026-07-08, 86 rows) found several of the old flat-list rule-based
heuristics (META_ATTR/DE_PARANGON/DE_QUANTIF/META_JUXT regexes) were WORSE than
chance (16.7% accuracy) — removed; only kept the handful of unambiguous
fixed-phrase rules (COMME_SI, COMP_DEG, MOD_ANALOG) that don't require
structural judgment calls.

Input:  figuratifs_task1_own.csv — built by build_figurative_cases.py from OUR
        OWN Task 1 (qwen3) référentiel/figuré results, NOT the old
        métaphores_identifiées_gpt.csv (Joanna's ChatGPT-based figurative
        set — wrong input, found 2026-07-09: only ~half overlaps with our
        own Task 1 figuré rows). Per Riccardo (2026-06-25 meeting): "you
        should use yours [not Joanna's ChatGPT results]." Re-run
        build_figurative_cases.py once Task 1 plantes finishes to refresh
        this file before scaling to the full corpus.
Output: resultats_task2_subcategories.csv
"""

import os, csv, re, json, time, requests
from collections import Counter

OLLAMA_URL  = "http://localhost:11434/api/chat"
MODEL       = "qwen3:30b"
INPUT_FILE  = os.path.expanduser("~/ecopoetique/métaphore/figuratifs_task1_own.csv")
OUTPUT_FILE = os.path.expanduser("~/ecopoetique/métaphore/resultats_task2_subcategories.csv")
LOG_FILE    = os.path.expanduser("~/ecopoetique/métaphore/task2_progress.log")
CHECKPOINT  = 50  # save every N rows
TIMEOUT     = 300

# ── 12 SUBCATEGORIES — current as of 2026-10-13 (Jul13 simplification + ───
# ── Sep17 MOD_ANALOG restoration, see file header) ──────────────────────────
SUBCATEGORIES = {
    "COMP_SIM":   ("comparaison similative",   "Adj/V + comme + SN",             "rusé comme un renard ; courir comme un lièvre"),
    "COMP_P":     ("comparaison phrastique",   "P1 comme P2",                    "les branches craquaient comme les os d'un vieux cerf"),
    "COMP_Q":     ("comparaison quantitative", "plus/moins/aussi/autant que",    "plus lent qu'une tortue ; plus haut qu'un séquoia"),
    "META_DET":   ("métaphore déterminative",  "N1 de N2, N1 métaphorisant",     "une forêt de pylônes ; un essaim de pensées ; pomme de discorde"),
    "META_QUAL":  ("métaphore qualificative",  "N1 de N2, N2 métaphorisant",     "une mémoire d'éléphant ; une mer de soie ; ventre de pastèque"),
    "META_NOM":   ("métaphore nominale",       "N1 est N2",                      "cet homme est un loup ; cette ville est une fourmilière"),
    "META_APP":   ("métaphore appositionnelle","apposition / juxtaposition / binôme nominal", "la montagne sentinelle ; le fleuve serpent ; arbre-parapluie ; forêt cathédrale"),
    "META_PRED":  ("métaphore prédicative",    "verbe OU adjectif incompatible", "la forêt avalait la lumière ; le glacier agonisait ; une douceur végétale"),
    "MOD_ANALOG": ("analogie modalisée",       "sembler, on dirait, avoir l'air de", "on aurait dit une meute de nuages"),
    "COUL":       ("couleur",                  "couleur + référent du vivant",   "vert pomme ; bleu ciel"),
    "LOC_IDIOM":  ("locution idiomatique",     "expression figée",               "avoir la chair de poule ; poser un lapin"),
    "IMAG":       ("représentation",           "image, dessin, sculpture, motif","un tableau représentant un lion ; une robe à fleurs"),
}

VALID_CODES = list(SUBCATEGORIES.keys())

# ── RULE-BASED PRE-FILTER — REMOVED 2026-07-09, then ONE rule reinstated ────
# Gold validation showed the "safe" fixed-phrase regexes (COMME_SI/COMP_DEG/
# MOD_ANALOG) were 0/7 (0%) at gold-check — because `context` is often a full
# multi-sentence paragraph and the regex matches ANY occurrence of the
# trigger phrase anywhere in it, not just the clause around the token. All
# classification was routed to the LLM as a result.
#
# 2026-07-09 (later): found `métaphore/liste_expressions.csv` — a 72-entry
# curated lexicon of genuinely fixed French animal idioms (built by Joanna's
# team pre-Task-2, e.g. "poser un lapin", "rusé comme un renard") with the
# exact token_lexique each maps to, and `filter_idiomatic.py` which already
# used it upstream for a different purpose. This is a real, pre-existing,
# hand-curated resource — not a regex guess — so unlike the removed rules,
# an EXACT case-insensitive substring match of one of these 65 known fixed
# expressions is high-precision by construction (these are established
# idioms, not coincidental phrase co-occurrence). Reinstated as the only
# rule, scoped to require the literal idiom string in the token's own
# sentence-local context (still whole `contexte` field, but the match target
# is a multi-word fixed phrase, not a short generic pattern, so the false-
# positive-from-elsewhere-in-paragraph risk that killed the old rules is
# much lower).
IDIOM_LEXICON_PATH = os.path.expanduser("~/ecopoetique/métaphore/liste_expressions_figées.txt")
try:
    with open(IDIOM_LEXICON_PATH, encoding="utf-8") as _f:
        KNOWN_IDIOMS = [line.strip().lower() for line in _f if line.strip()]
except FileNotFoundError:
    KNOWN_IDIOMS = []

# 2026-10-19: two more deterministic pre-filters added after analyzing the
# real 184-row gold-validation confusion matrix (resultats_task2_gold_validation.csv,
# 69.0%). Both were dry-tested against gold_task2_task45_CURRENT.csv BEFORE
# being wired in here (recall + false-fire count checked row by row), per the
# project's own standing lesson that a plausible-looking regex can be worse
# than chance if it matches anywhere in a multi-sentence context instead of
# near the token itself (exactly what killed the original 2026-07-09
# rule-based layer). A third candidate rule — a bare "plus/moins/aussi/autant
# ... que" window check for COMP_Q — was dry-tested the same way and REJECTED:
# it only recalled 2/6 genuine COMP_Q gold rows, while wrongly overriding 2
# already-correct LOC_IDIOM rows ("les carottes sont cuites", "plus figue que
# raisin" — both contain "plus...que" coincidentally, not as a real degree
# comparison of the figurative token). Net zero gain with real regression
# risk at full-corpus scale, so it was NOT added — this needs real syntactic
# parsing (does "que" actually introduce the token's own comparison clause),
# not a proximity regex, to do safely.
def _window_around_token(context, token, radius):
    ctx = context.lower()
    tok = token.lower()
    idx = ctx.find(tok)
    if idx == -1:
        return ctx
    start = max(0, idx - radius)
    end = min(len(ctx), idx + len(tok) + radius)
    return ctx[start:end]

# Fixed vocative endearments → LOC_IDIOM (Riccardo 2026-10-15: "mon loup"/"ma
# poule" etc. used to ADDRESS someone affectionately are frozen vocabulary).
# Window-scoped with a negative lookahead for a following "de": a bare
# substring match on "mon loup" anywhere in context wrongly fired on gold
# id=116 ("mon loup de père" — a META_DET construction, "mon wolf-ish father",
# not a vocative address) before this fix; confirmed 0 false fires across the
# full 184-row gold set after adding the "(?!\s+de\b)" exclusion.
_ENDEARMENT_RE = re.compile(r"\b(mon loup|ma poule|mon chou|mon lapin|ma biche)\b(?!\s+de\b)")

# "traiter (qqn) de X" / naming-verb constructions → META_NOM (Riccardo
# 2026-10-15: always META_NOM, even non-standard insult lists like "traiter de
# bougnoules, de bicots, d'oignons"). Handles French elision ("d'oignons", not
# "de oignons") and a wide window, since enumerated-list contexts can put the
# triggering verb 40-60 chars before the actual token. Confirmed 1/30 recall
# (gold id=37) with 0 false fires across the full 184-row gold set.
_TRAITER_RE = re.compile(r"\btrait(?:er|é|ée|és|ées|ait|ant|erent|èrent|era)\b[^.!?]{0,60}?\b(?:de\b|d['’])")

# The 3 idioms added 2026-10-19 ("pomme de discorde", "mi-figue mi-raisin",
# "à pas de loup") — excluded in use_new_rules=False mode so that mode
# reproduces the exact pre-2026-10-19 (gold-slips-fixed, "PRE_FIX", 69.0%)
# rule layer, bugs included, for a clean side-by-side isolation test.
_NEW_IDIOMS_20261019 = {"pomme de discorde", "mi-figue mi-raisin", "à pas de loup"}
KNOWN_IDIOMS_ORIGINAL = [e for e in KNOWN_IDIOMS if e not in _NEW_IDIOMS_20261019]

def rule_based_classify(token, context, use_new_rules=True):
    # 2026-10-19: window-scoped, not a bare substring over the full (often
    # multi-sentence) context. Found via gold smoke-test: id=82 "oignons"
    # (gold META_NOM) was wrongly firing LOC_IDIOM because the SAME long
    # paragraph happens to also contain "dans la gueule du loup" (a real
    # lexicon entry) nowhere near the actual token — a pre-existing bug in
    # this check, not something introduced by the two rules below. Window-
    # scoping confirmed 3/3 correct, 0 false fires across the full 184-row
    # gold set (vs. 3/4 correct, 1 false fire with the old whole-context match).
    #
    # use_new_rules=False reproduces the exact PRE_FIX (2026-10-19, 69.0%)
    # rule layer instead — bare substring over the full context, original
    # 65-entry lexicon, no endearment/traiter-de rules — so a side-by-side
    # run against it isolates the COMP_SIM/COMP_P verifier's own effect from
    # today's other rule-layer changes. See CLAUDE.md-style "isolate one
    # variable" discipline.
    if not use_new_rules:
        ctx = context.lower()
        for expr in KNOWN_IDIOMS_ORIGINAL:
            if expr in ctx:
                return "LOC_IDIOM"
        return None

    window60 = _window_around_token(context, token, 60)
    for expr in KNOWN_IDIOMS:
        if expr in window60:
            return "LOC_IDIOM"
    if _ENDEARMENT_RE.search(_window_around_token(context, token, 40)):
        return "LOC_IDIOM"
    if _TRAITER_RE.search(_window_around_token(context, token, 70)):
        return "META_NOM"
    return None  # uncertain → send to LLM

# ── LLM PROMPT — sequential decision-tree, not a flat 19-way pick ───────────
def make_prompt(token, context, category):
    return f"""Tu es expert en stylistique française et en figures de style.

Le mot «{token}» (catégorie: {category}) est utilisé de façon FIGURATIVE dans ce contexte:
«{context}»

Détermine la catégorie structurelle de cette figure en suivant CET ORDRE de
questions (comme un arbre de décision — réponds à la première question qui
s'applique, ne compare pas toutes les catégories en même temps).
⚠ DISCIPLINE D'ORDRE OBLIGATOIRE : teste les questions UNE PAR UNE, dans
l'ordre numéroté. Dès qu'une question s'applique clairement, réponds avec
son code et ARRÊTE-TOI — ne continue pas à évaluer les questions suivantes
"au cas où" une autre catégorie semblerait mieux correspondre.

1. Y a-t-il une expression figée/lexicalisée où «{token}» a perdu son sens
   littéral d'animal/plante ? Quelques exemples illustrant des FORMES variées
   que peut prendre une expression figée (le point commun n'est pas la forme
   syntaxique mais le fait que le sens global est FIXÉ par l'usage, indépendant
   du sens propre de chaque mot) :
   - avec "comme" : "rusé comme un renard", "muet comme une carpe"
   - avec "de" : "larmes de crocodile", "rat de bibliothèque", "travail de fourmi"
   - nom composé : "bouc émissaire", "chant du cygne"
   - locution verbale : "avoir la chair de poule", "poser un lapin",
     "avoir une araignée au plafond", "avoir des fourmis dans les jambes/les
     muscles" (sensation de picotement/fourmillement, pas de vraies fourmis)
   ⚠ EXCLUS de LOC_IDIOM — vérifie ces cas AVANT de conclure LOC_IDIOM,
   même si l'expression "a l'air" figée. Si l'un s'applique, va directement
   à la question indiquée plutôt que de répondre ici :
   - L'expression sert à COULEUR (ex: "poivre et sel" pour des cheveux) →
     ne réponds PAS ici, va à la question 2 (COUL).
   - Après "comme", le nom garde un sens LITTÉRAL actif dans la scène, OU
     "comme" introduit une proposition entière décrivant un ÉVÉNEMENT/
     PROCESSUS (même via une proposition relative ou un participe, pas
     seulement un verbe conjugué autonome) — ex: "se faire tirer comme des
     lièvres" (de vrais lièvres sont chassés), "comme on compte des
     moutons" (bien que "compter les moutons" soit aussi une expression
     connue, ICI c'est une comparaison vivante avec son propre verbe
     conjugué, pas une locution figée hors-contexte), "comme des baleines
     qu'on a abattues et dépecées" (proposition relative décrivant un
     événement) → ce n'est PAS une locution figée mais une comparaison
     vivante, ne réponds PAS ici, va à la question 4 (COMP_Q) ou 5
     (COMP_SIM/COMP_P). RÈGLE GÉNÉRALE : si "comme X" peut être développé en
     une proposition avec un événement/processus concret (même implicite ou
     elliptique), préfère la question 5 (COMP_P) à LOC_IDIOM, même si "comme
     X" ressemble aussi à une expression connue par ailleurs.
     ⚠ AUTO-VÉRIFICATION OBLIGATOIRE avant de répondre LOC_IDIOM : retire
     mentalement "comme" + le mot-clé de la phrase. Reste-t-il un événement
     ou une action CONCRÈTE et LITTÉRALE décrite dans le passage (des morts,
     une chasse, un mouvement réel, une action accomplie SUR le mot-clé) ?
     Si oui, ce n'est PAS LOC_IDIOM, quel que soit l'air "figé" de la
     tournure — c'est une comparaison vivante (question 4 ou 5). Ne réponds
     LOC_IDIOM que si retirer la comparaison ne changerait RIEN au sens
     factuel de la phrase.
   - Le contexte décrit une représentation/symbole (photo, motif, dessin,
     objet décoratif) plutôt qu'un usage figuré de langage (ex: "fleurs de
     lis" sur un drapeau, "à l'eau de rose" en référence à des photos
     sentimentales) → ne réponds PAS ici, va à la question 3 (IMAG).
   - La tournure est une RESSEMBLANCE-SEULEMENT du type "n'avoir de X que
     l'aspect/le nom/l'air" (ex: "qui n'a de concombre que l'aspect") →
     même si ça "a l'air" d'une expression figée, ne réponds PAS ici, va à
     la question 6 (MOD_ANALOG) — cette tournure est structurellement une
     analogie modalisée (ressemblance de surface, pas un sens lexicalisé
     figé), pas une locution.
   - L'expression COMBINE ou MODIFIE une locution connue de façon créative
     plutôt que de la citer dans sa forme EXACTE et figée (ex: "le cimetière
     des moutons noirs" fusionne deux expressions connues — "cimetière des
     éléphants" et "mouton noir" — en quelque chose de nouveau ; "la pomme
     du péché" est une référence symbolique mais n'est PAS la forme figée
     exacte, qui serait "le fruit défendu" ; "mon buisson ardent" est un
     usage créatif, pas idiomatique dans ce contexte), OU l'expression n'a
     PAS de sens figé conventionnel attesté et semble inventée pour
     l'occasion → ne réponds PAS LOC_IDIOM, va à la question 9 (META_NOM).
     RÈGLE GÉNÉRALE (confirmée par le chercheur superviseur) : préfère
     META_NOM à LOC_IDIOM dès que l'expression n'est pas EXACTEMENT sa forme
     canonique figée — une reprise, une recombinaison, une modification ou
     un usage créatif en fait une métaphore vivante, pas un idiome figé.
   Si aucun de ces cas ne s'applique → LOC_IDIOM.
2. «{token}» désigne-t-il une COULEUR (ex: "vert pomme", "bleu ciel") plutôt
   qu'un être vivant ? → COUL
   ⚠ EXCLUS de COUL si ce n'est pas «{token}» lui-même qui nomme une couleur,
   mais un ADJECTIF DE COULEUR séparé appliqué au sujet dans une comparaison
   de degré (ex: "aussi blond que les blés" — c'est "blond" qui est un terme
   de couleur, pas «blés», et la structure "aussi...que" est une comparaison
   de degré) → ne réponds PAS ici, va à la question 4 (COMP_Q).
3. Le contexte décrit-il une REPRÉSENTATION du vivant — pas seulement une
   image/dessin/sculpture explicite, mais aussi une simple RESSEMBLANCE DE
   FORME/silhouette avec le vivant, un DÉGUISEMENT ("déguisé/habillé/costumé
   en" + «{token}» — ex: "des chiens que l'on déguise en éléphants nains" =
   les chiens ont la FORME/l'apparence d'éléphants, pas de vrais éléphants),
   un MOTIF DÉCORATIF sur un objet/vêtement ("parsemé de", "orné de",
   "décoré de", "à motifs de" + «{token}»), OU une ÉVOCATION d'une figure/
   d'un titre/d'un symbole CULTUREL, LITTÉRAIRE, MYTHOLOGIQUE ou de CONTE
   déjà connu et associé au vivant, plutôt qu'une comparaison vivante
   inventée dans ce passage (ex: "le Roi des Aulnes" — référence au titre/
   personnage légendaire, pas une nouvelle métaphore ; "la princesse au
   petit pois" — référence au conte ; un vitrail ou vers biblique citant
   "la vigne") (ex: "un tableau représentant un lion" ; "une tache en forme
   de haricot" ; "des motifs à fleurs de lis") — plutôt que le vivant
   lui-même agissant ou étant décrit dans une scène vivante ? → IMAG.
   ⚠ Vérifie ce cas AVANT la question 7 (META_APP) et la question 8
   (structure "N de N2") — une simple juxtaposition de noms ("citrouille
   gomme à effacer", "Fenrir, loup géant") a la FORME d'une apposition
   (question 7) mais si le sens est une RESSEMBLANCE DE FORME ou une
   RÉFÉRENCE CONNUE plutôt qu'une caractérisation vivante, c'est IMAG, pas
   META_APP. De même, "parsemée de tournesols" a la forme d'un "N de N2"
   mais désigne un motif décoratif, donc IMAG, pas META_QUAL (question 8).
   ⚠ EXCLUS de IMAG — même si «{token}» évoque une référence culturelle/
   biblique/littéraire connue — si la phrase a par ailleurs une COPULE
   D'IDENTITÉ explicite ("est/sont/était/c'est"...) ou un VERBE/ADJECTIF
   dont le sens est incompatible avec «{token}» : dans ce cas la référence
   culturelle est secondaire, et la question 9 (META_NOM, si copule) ou 10
   (META_PRED, si verbe/adjectif incompatible) doit primer. Ex: "l'ivraie sera jetée
     au feu" (référence biblique MAIS «sera jetée» est un verbe appliqué
     métaphoriquement à l'ivraie pour désigner les pécheurs) → META_PRED,
     pas IMAG simplement parce que la scène a une origine biblique. La
   référence culturelle ne déclenche IMAG que si AUCUNE autre structure
   (copule, verbe incompatible) n'explique mieux la figure.
   ⚠⚠ MAIS cette exclusion NE S'APPLIQUE PAS si la copule se contente
   d'IDENTIFIER la figure culturelle/mythologique elle-même à son propre
   sujet grammatical — sans introduire de référent réel DIFFÉRENT auquel
   on la compare. Teste : le sujet de la copule EST-IL déjà la figure
   culturelle elle-même (autre pronom/nom qui la désigne, pas une personne
   ou un objet distinct du passage) ? Si oui → reste IMAG malgré la copule.
   Si le sujet est un référent réel autre que la figure elle-même → META_NOM.
   Ex: "Fenrir, loup géant... c'est le loup qui tuera Odin" (le sujet de
   "c'est" est Fenrir lui-même, la copule ne fait que redire son identité
   mythologique déjà établie) → IMAG. Mais "Riccardo, c'est le loup qui
   tuera Odin" (le sujet "Riccardo" est une personne réelle DIFFÉRENTE du
   loup mythologique, comparée à lui) → META_NOM.
4. Y a-t-il une comparaison de degré ("plus/moins/aussi/autant... que") ? → COMP_Q
5. Y a-t-il "comme" (y compris "comme si") ? Regarde ce qui suit "comme" et
   ce que «{token}» (ou le groupe nominal qui le contient) FAIT ou SUBIT :
   - Une résemblance STATIQUE/qualitative simple, SANS processus ni action —
     «{token}» est juste décrit comme ressemblant à quelque chose, sans
     qu'aucun événement ne lui arrive (ex: "rusé comme un renard", "comme
     les tentacules d'une pieuvre") → COMP_SIM
   - Une comparaison où le vivant comparé SUBIT ou ACCOMPLIT une ACTION, un
     PROCESSUS ou un ÉVÉNEMENT — que ce soit via un verbe conjugué autonome,
     une proposition relative, OU un participe/gérondif décrivant ce
     processus (ex: "comme les os craquent" ; "comme si une forêt retenait
     son souffle" ; "comme des roses... finissant par composer un bouquet"
     — les roses SUBISSENT un devenir/une transformation ; "comme une
     araignée fouettée" — l'araignée SUBIT l'action d'être fouettée, même
     si "fouettée" est un participe et non un verbe pleinement conjugué ;
     "comme des baleines qu'on a abattues et dépecées") → COMP_P
   ⚠ Le test n'est PAS "y a-t-il un verbe conjugué séparé" mais "le vivant
   comparé subit-il/accomplit-il quelque chose (même exprimé par un
   participe ou une proposition relative), ou est-il juste décrit de façon
   statique" ? Processus/action → COMP_P. Simple trait statique → COMP_SIM.
   ⚠ ATTENTION : un simple ADJECTIF ("un olivier fourbu") ou une phrase
   prépositionnelle IDENTIFIANTE ("le chien DE LA BRIGADE CANINE") qui
   modifie le nom comparé SANS décrire d'action/processus NE DÉCLENCHE PAS
   COMP_P — reste COMP_SIM. Seul un participe/proposition relative décrivant
   un évènement SUBI (comme "fouettée", "qu'on a abattues") déclenche COMP_P ;
   un adjectif ou "de X" qui ne fait que PRÉCISER/IDENTIFIER le nom (quel
   olivier, quel chien) ne compte pas comme un processus.
6. Y a-t-il "sembler", "on dirait", "avoir l'air de", "faire l'effet de", ou
   une tournure équivalente de perception/auto-perception analogique
   ("se voir", "se sentir devenir", "s'imaginer en"), OU une tournure de
   RESSEMBLANCE-SEULEMENT du type "n'avoir de X que l'aspect/le nom/l'air"
   (ex: "qui n'a de concombre que l'aspect" = ne ressemble au concombre que
   par l'apparence, sans en être vraiment un), OU "ressemblance/ressembler
   à/avec" + «{token}» (ex: "la ressemblance du Lockheed Vega avec un
   aigle"), OU "des airs de" + «{token}» (variante plurielle d'"avoir l'air
   de" — ex: "des airs implorants de chat") ? → MOD_ANALOG
7. «{token}» est-il placé JUSTE À CÔTÉ d'un nom (sujet ou complément) SANS
   copule ("est/était"), SANS "de" — une simple apposition, épithète directe,
   OU mot composé/juxtaposition directe avec ou sans trait d'union (ex: "la
   montagne sentinelle", "poulpe enfiévré tournoyant dans ma bouche",
   "arbre-parapluie", "forêt cathédrale") ? → META_APP. Ce cas couvre aussi
   ce qu'on appelait autrefois META_JUXT (catégorie éliminée le 2026-07-10
   sur confirmation de Riccardo — tout binôme nominal/juxtaposition va
   désormais dans META_APP). Ce cas doit être écarté AVANT de considérer
   "N1 de N2" ci-dessous — ne choisis META_DET/META_QUAL/META_NOM que si une
   vraie copule ou un vrai "de" relie les deux noms.
   ⚠ EXCLUS de META_APP si le sens est une RESSEMBLANCE DE FORME ou une
   RÉFÉRENCE CULTURELLE/LITTÉRAIRE CONNUE plutôt qu'une caractérisation
   vivante (voir question 3, IMAG) — re-vérifie la question 3 avant de
   répondre ici si ce doute existe.
8. Y a-t-il une structure "N1 de N2" (sans "comme") ? La question n'est PAS
   le domaine sémantique du trait illustré (qualité vs matière vs catégorie
   sociale...) mais une question PUREMENT POSITIONNELLE : «{token}» occupe-t-
   il la place de N1 (avant "de") ou de N2 (après "de") ?
   - «{token}» = N1, le terme vivant METAPHORISE N2 (ex: "une forêt de
     pylônes" — forêt=N1 métaphorise les pylônes ; "pomme de discorde" —
     pomme=N1 métaphorise la discorde ; "un essaim de pensées" — essaim=N1
     métaphorise les pensées) → META_DET
   - «{token}» = N2, le terme vivant est utilisé pour QUALIFIER N1 (ex:
     "une mémoire d'éléphant" — éléphant=N2 qualifie la mémoire ; "une mer
     de soie" — soie n'est pas vivant mais même logique inversée ; "ventre
     de pastèque" — pastèque=N2 qualifie le ventre) → META_QUAL
   ⚠ C'est un test de POSITION, pas de sens : regarde seulement si «{token}»
   est avant ou après "de" dans cette structure précise, rien d'autre.
   ⚠ EXCLUS de META_DET/META_QUAL si la structure "N1 de N2" ENTIÈRE (le
   groupe nominal complet, pas juste le lien interne) est elle-même placée
   en APPOSITION à un AUTRE nom plus large (ex: "sa tête, boule de piquants
   noirs" — ce n'est pas "piquants noirs" qui qualifie "boule" en isolation,
   c'est le groupe ENTIER "boule de piquants noirs" qui est apposé à "tête"
   pour la décrire) → ne réponds pas ici, retourne à la question 7
   ⚠ EXCLUS également si la structure "N1 de N2" ENTIÈRE est l'ATTRIBUT d'une
   COPULE qui porte sur un AUTRE référent plus large dans la même phrase (ex:
   "ses yeux... avec deux grains DE CASSIS" où "deux grains de cassis"
   identifie "ses yeux" ; "je serai... la feuille DU BANANIER" où "je" est
   identifié à "la feuille du bananier" via "serai") — ici c'est la COPULE
   (être/serai/sera/étaient...) qui gouverne l'identification à l'échelle de
   la phrase, PAS le lien interne "de" entre «{token}» et l'autre nom ; la
   structure "de" ne fait que préciser LEQUEL objet est identifié, elle n'est
   pas elle-même la figure. → ne réponds pas ici, va à la question 9 (META_NOM)
   (META_APP) et traite tout le groupe "N de N2" comme l'élément apposé.
   Test : y a-t-il un AUTRE nom, séparé par une virgule ou juste avant, que
   le groupe "N de N2" entier vient décrire/renommer ? Si oui → META_APP au
   niveau du groupe entier, pas META_QUAL au niveau du "de" interne.
   ⚠ EXCLUS de META_DET/META_QUAL si le "N de N2" est en fait la partie
   prédicative d'une copule d'IDENTITÉ ("il est LE X de N2", "elle est
   celle de N2" — la phrase affirme une identité, pas juste une relation
   N1-de-N2) → ne réponds pas ici, va plutôt à la question 9 (META_NOM).
   Ex: "il est le cerf de ma vie" (affirmation d'identité "il EST le
   cerf") → META_NOM, pas META_DET/META_QUAL.
   ⚠ EXCLUS de META_DET/META_QUAL si N1 est un nom-écran de RESSEMBLANCE
   ("forme", "aspect", "sorte", "genre", "espèce", "air", "façon" — ex: "en
   forme de palmiers", "une sorte de dragon") : ce n'est pas N1 qui est
   qualifié par N2, c'est une comparaison de ressemblance équivalente à
   "comme N2" → traite comme COMP_SIM (question 5), pas META_QUAL.
9. Y a-t-il une copule "est/était/sont/sommes/c'est/ce sont/serai.../fut/
   fussent/soit" (toute forme ou temps de "être", y compris l'INFINITIF
   "être" après un verbe modal/de préférence : "mieux vaut être X",
   "veut/voudrait être X", "doit être X"), OU "devenir/redevenir", OU un
   surnommage/désignation identifiante (ex: "on le surnomme le rat", "on
   l'appelle la vipère", "on le traite de macaque" — «{token}» devient
   littéralement le nom/surnom donné à quelqu'un), OU une EXCLAMATION
   insultante/caractérisante du type "quel/quelle N1 de N2 !" visant une
   personne/un animal précis déjà présent dans la scène (ex: "quel têtard
   de quelle mare !" — insulte qui NOMME la personne par ce terme, comme
   "quel idiot !") ? → META_NOM
   Exemples : "cet homme est un loup" ; "nous sommes de grosses côtes de
   bœuf" ; "c'est le cygne et le chat qui se nettoient" ; "Constance
   redevint un agneau" ; "mieux vaut être une mouette qu'une huître".
   ⚠ COMPTE AUSSI COMME COPULE D'IDENTITÉ (→ META_NOM), même sans "être"
   explicite adjacent à «{token}» :
   - un DÉTERMINANT DÉMONSTRATIF ("ce/cette/cet") introduisant «{token}»
     pour identifier directement un référent réel précis (ex: "j'étais ce
     chamois effaré" ; "cette antilope qui cherche une source" ; "ce
     haricot rouge doré" désignant une partie du corps) — le démonstratif
     fonctionne ici comme une identification, au même titre que "est".
   - une forme SUBJONCTIVE/CONCESSIVE de "être" ("fussent-ils des chiens",
     "fût-elle un ange") qui affirme quand même une identité de façon
     concessive ("même si/en admettant qu'ils étaient X") — à ne pas
     confondre avec le cas hypothétique "si X était Y" exclu ci-dessous,
     qui lui pose une hypothèse non affirmée.
   ⚠ EXCLUS de META_NOM si la copule est au conditionnel/hypothétique
   ("si X était Y, ..." — une hypothèse, pas une affirmation d'identité) :
   va plutôt à la question 5 (COMP_P, "comme si" couvre aussi ce cas).
   ⚠ EXCLUS de META_NOM — ne réponds PAS ici, même avec une copule
   explicite, dans ces 2 cas (le prédicat/l'attribut a sa PROPRE structure
   figurative plus spécifique, qui doit primer sur la copule générique) :
   - Le nom attribut est lui-même une EXPRESSION FIGÉE/IDIOME connu, ou a
     sa propre structure "N1 de N2" déjà couverte par la question 8 (ex:
     "je suis un cœur d'artichaut" — idiome fixe ; "la langue chinoise
     était un sésame" — référence à "Sésame, ouvre-toi") → va plutôt à la
     question 1 (LOC_IDIOM) ou reste sur la réponse de la question 8.
   - «{token}» est un TERME D'AFFECTION/D'ADRESSE figé ("mon loup", "ma
     poule", "mon chou", "mon lapin" utilisés pour s'adresser affectueusement
     à une personne précise, PAS pour la caractériser ou l'insulter) → ces
     termes sont du vocabulaire affectif FIGÉ → va plutôt à la question 1
     (LOC_IDIOM). Contraste : "on le traite de rat" (insulte qui
     CARACTÉRISE la personne) → reste META_NOM. "mon loup" (appellation
     affectueuse neutre) → LOC_IDIOM.
   ⚠ DISTINCTION AVEC META_PRED (question 10, juste après) : si «{token}»
   est lui-même le SUJET ou l'ATTRIBUT d'une copule d'identité (le mot-clé
   EST ce qu'on affirme) → META_NOM (ex: "cet homme est un loup",
   "j'ai engendré un chicon" — chicon est l'identité/le produit affirmé,
   pas une action). Si «{token}» est plutôt le sujet d'un VERBE D'ACTION ou
   le support d'un ADJECTIF normalement incompatible avec lui, même si une
   copule existe ailleurs dans la phrase → META_PRED (ex: "le chêne a
   répliqué" — chêne accomplit l'action humaine de répliquer, ce n'est pas
   une identité affirmée).
10. Y a-t-il un VERBE dont le sens littéral est incompatible avec son sujet,
    OU un ADJECTIF normalement réservé à un autre domaine appliqué à
    «{token}» (ex: "la forêt avalait la lumière", "le glacier agonisait",
    "le chêne a répliqué", "une douceur végétale" — «{token}» accomplit une
    ACTION ou reçoit une QUALIFICATION qui lui est normalement étrangère,
    plutôt que de simplement RECEVOIR une identité/un nom via une copule) ?
    → META_PRED

Réponds UNIQUEMENT avec ce JSON (indique aussi le numéro de question qui a
déclenché ta réponse, pour vérification) :
{{"code": "CODE", "question_number": N, "raison": "explication courte en français"}}"""

# ── OLLAMA CALL ───────────────────────────────────────────────────────────────
def call_ollama(prompt, temperature=0):
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": 8000, "num_ctx": 16384},
        }, timeout=TIMEOUT)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        m = re.search(r'\{.*?\}', content, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
                code = data.get("code","").strip().upper()
                raison = data.get("raison","").strip()
                if code in VALID_CODES:
                    return code, raison
            except json.JSONDecodeError:
                # found 2026-10-13 (24-row Task 2 smoke test, id=19 "singes"):
                # qwen3 sometimes emits a bare backslash or other invalid
                # escape inside "raison" (free-form French text, not code),
                # which breaks strict JSON parsing even though "code" itself
                # is fine. Fall back to regex-extracting just the code field
                # directly rather than discarding a response that otherwise
                # classified correctly.
                cm = re.search(r'"code"\s*:\s*"([A-Z_]+)"', m.group(0))
                if cm and cm.group(1) in VALID_CODES:
                    return cm.group(1), "(raison unparseable, bad escape)"
        # Try to find any valid code in response
        for code in VALID_CODES:
            if code in content:
                return code, ""
        return "UNKNOWN", content[:100]
    except Exception as e:
        return "ERROR", str(e)[:80]

# LOC_IDIOM gate — TRIED 2026-10-19, REVERTED 2026-10-20 (see classify_figurative's
# own comment for the live gold-set numbers that killed it: 3/14 correct with
# the gate vs. a simulated 8/14 without it). The idea (re-ask excluding
# LOC_IDIOM when the lexicon doesn't back it up) was sound in principle but
# the 68-entry lexicon is too incomplete to use as gating evidence — "not in
# the list" mostly meant "list has gaps," not "model is over-triggering."
# Removed rather than left disabled; don't re-add this exact mechanism
# without first meaningfully expanding the idiom lexicon.

# 2026-10-20: narrow binary verifier for COMP_SIM vs COMP_P — the single
# biggest confusable PAIR in the real 184-row gold confusion matrix (7 of 57
# errors, all COMP_SIM->COMP_P) — TRIED 2026-10-20, REVERTED same day.
# Isolated on its own (PRE_FIX rule layer + verifier only, no other change):
# 69.0% -> 64.1% on a full 184-row run — a ~5pp drop, far outside the ~0.6pp
# swing seen between identical-code reruns elsewhere in this project, so a
# real effect, not noise. Same failure shape as the LOC_IDIOM gate above:
# a second, narrower call overriding an already-correct first answer more
# often than it fixes a wrong one, even though it was dry-tested in reasoning
# (not against live model behavior, which is what actually mattered) and
# avoided the generic "check your own answer" anti-pattern by design. Second
# confirmed case in this file of a second-opinion LLM call net-hurting Task 2
# — treat that as a real pattern for this task, not a fluke: don't re-add a
# verifier/gate style re-ask without a non-LLM (deterministic) signal behind
# it, the same lesson the LOC_IDIOM gate already taught.

def classify_figurative(token, context, category, use_new_rules=True):
    """Full Task 2 classification: rule pre-filters -> LLM. Returns
    (code, raison, method).
    use_new_rules=False reproduces the exact PRE_FIX (69.0%) rule layer
    instead of today's extended one — see rule_based_classify's own comment.
    """
    code = rule_based_classify(token, context, use_new_rules=use_new_rules)
    if code is not None:
        return code, "règle syntaxique", "rule"

    prompt = make_prompt(token, context, category)
    code, raison = call_ollama(prompt)
    # 2026-10-20: the LOC_IDIOM gate (re-ask excluding LOC_IDIOM when not
    # lexicon-backed) was tried and REVERTED after live gold-set testing.
    # It fired 14 times on the first ~97 rows of a 184-row run; only 3 were
    # correct. 8 of the 14 had gold==LOC_IDIOM — the model's original answer
    # was ALREADY right, and the gate wrongly forced it away because that
    # specific idiom (e.g. "se prendre une prune", "sésame"/"ouvre-toi",
    # idiomatic "chien"/"gardon" uses) isn't in our 68-entry lexicon.
    # "Not in an incomplete lexicon" turned out not to be reliable evidence
    # of over-triggering — it mostly just meant the lexicon has gaps.
    # Simulated removing the gate on that same 14-row sample: 3/14 -> 8/14
    # correct. Keep the lexicon/endearment/traiter-de PRE-filters (those were
    # independently dry-tested and confirmed clean) — only the POST-hoc gate
    # on the LLM's free-form LOC_IDIOM answer is removed. Revisit only after
    # the idiom lexicon itself is meaningfully expanded (not just these 3
    # entries), not by re-adding this same gate logic.
    return code, raison, "llm"

# ── SELF-CONSISTENCY / MAJORITY VOTE — added 2026-10-16 ─────────────────────
# Research-backed (self-consistency literature): majority voting across N
# samples at temperature>0 helps *when single-call accuracy is already above
# ~50%* (ours is ~63-64%) — below that threshold it can hurt instead. Never
# edits the prompt itself, so it carries none of the ripple-effect risk that
# every shared-prompt-text edit caused today for Task 2. Also directly
# targets a real phenomenon found today: identical code, same row, flipping
# between correct/incorrect across separate runs (e.g. "piquants noirs") —
# that's exactly the per-sample noise majority voting is meant to cancel out.
def call_ollama_voted(prompt, n=5, temperature=0.7):
    from collections import Counter
    votes = []
    last_raison = ""
    for _ in range(n):
        code, raison = call_ollama(prompt, temperature=temperature)
        if code in VALID_CODES:
            votes.append(code)
            last_raison = raison
    if not votes:
        return "ERROR", "no valid votes across all samples"
    winner, count = Counter(votes).most_common(1)[0]
    return winner, f"{count}/{len(votes)} votes | {last_raison}"

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    # Load input
    with open(INPUT_FILE, encoding='utf-8') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    print(f"Total figurative cases: {len(rows)}")

    # Load already done
    done = set()
    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding='utf-8') as f:
            existing = list(csv.DictReader(f))
            done = {(r['fichier'], r['token_lexique'], r['contexte'][:50]) for r in existing}
        print(f"Already done: {len(done)} — resuming")

    # Open log
    log = open(LOG_FILE, 'a', encoding='utf-8')

    fields = ['fichier','token_lexique','contexte','categorie','lemme',
              'decision','subcategory','method','raison']

    # Open output in append mode
    write_header = not os.path.exists(OUTPUT_FILE) or len(existing) == 0
    out_f = open(OUTPUT_FILE, 'a', newline='', encoding='utf-8')
    writer = csv.DictWriter(out_f, fieldnames=fields, extrasaction='ignore')
    if write_header:
        writer.writeheader()

    rule_count = llm_count = error_count = 0
    start = time.time()

    for i, row in enumerate(rows, 1):
        key = (row['fichier'], row['token_lexique'], row['contexte'][:50])
        if key in done:
            continue

        token   = row.get('token_lexique','').strip()
        context = row.get('contexte','').strip()
        cat     = row.get('categorie','').strip()

        code, raison, method = classify_figurative(token, context, cat)
        if method == "rule":
            rule_count += 1
        elif code in ("UNKNOWN", "ERROR"):
            error_count += 1
            code = "UNKNOWN"
        else:
            llm_count += 1

        out_row = {**row, 'subcategory': code, 'method': method, 'raison': raison}
        writer.writerow(out_row)
        out_f.flush()

        # Progress
        if i % 100 == 0:
            elapsed = time.time() - start
            rate = i / elapsed
            eta = (len(rows) - i) / rate / 3600
            msg = f"[{i:>5}/{len(rows)}] rule={rule_count} llm={llm_count} err={error_count} ETA={eta:.1f}h"
            print(msg)
            log.write(msg + '\n'); log.flush()

    out_f.close()
    log.close()

    # Final summary
    print(f"\n{'='*60}")
    print("TASK 2 — SUBCATEGORY DISTRIBUTION")
    print(f"{'='*60}")
    with open(OUTPUT_FILE, encoding='utf-8') as f:
        results = list(csv.DictReader(f))
    counts = Counter(r['subcategory'] for r in results)
    total = len(results)
    for code, n in sorted(counts.items(), key=lambda x: -x[1]):
        pct = n/total*100
        desc = SUBCATEGORIES.get(code, ("?","",""))[0]
        print(f"  {code:<18} {n:>5} ({pct:>5.1f}%)  {desc}")
    print(f"\n  Total: {total} | Rule-based: {rule_count} | LLM: {llm_count}")
    print(f"  Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
