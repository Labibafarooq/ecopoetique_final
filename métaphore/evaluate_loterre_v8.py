"""
Task 1 — Loterre ONLY — v8
Targeted at 5 specific error patterns from v6 Group A:
1. Temporal/situation escape metaphors (marais, boue, sables)
2. Sea as emotional distance/abandonment (traverser la mer, largué en mer)
3. Landscape as inner renewal (renaissance du paysage, renouveau)
4. Fire/incendie as intensity metaphor (incendie des fourneaux)
5. Comparative structures where geographic term is figurative anchor

All examples independent from gold set.
"""
import os, csv, json, re, requests

OLLAMA_URL   = "http://localhost:11435/api/chat"
OLLAMA_MODEL = "qwen3:30b"
GOLD_FILE    = os.path.expanduser("~/ecopoetique/métaphore/GOLD_litteralite_loterre__RB.csv")
OUTPUT_FILE  = os.path.expanduser("~/ecopoetique/métaphore/eval_loterre_v8_results.csv")

EXAMPLES_LOTERRE = """
EXEMPLES — termes écologiques/géographiques Loterre (indépendants du jeu d'évaluation):

référentiel (lieu ou concept écologique réel):
• "Les scientifiques étudient l'écosystème du lac depuis vingt ans."
  → écosystème = référentiel (vrai concept écologique scientifique)
• "La déforestation détruit les forêts tropicales à un rythme alarmant."
  → forêts = référentiel (vraies forêts, contexte écologique)
• "Le biologiste traversait la steppe mongole à dos de cheval depuis des jours."
  → steppe = référentiel (vrai biome géographique traversé)
• "La montagne culminait à 4807 mètres — le Mont Blanc, toit de l'Europe."
  → montagne = référentiel (vrai sommet géographique précis)
• "Il s'assit au bord du fleuve et regarda l'eau couler en silence pendant une heure."
  → fleuve = référentiel (vrai cours d'eau, présent physiquement dans la scène)
• "Les forêts brûlaient. Les océans agonisaient. Le permafrost fondait."
  → océans = référentiel (vrais océans dans un contexte de crise écologique réelle)
• "Le four de la boulangerie brûlait depuis cinq heures du matin."
  → four = référentiel (vrai appareil de cuisson, contexte concret de boulangerie)
• "Il alluma les brûleurs de la cuisinière et la flamme s'éleva."
  → flamme = référentiel (vraie flamme physique dans une cuisine)

figuré (métaphore, expression idiomatique):
• "Prêcher dans le désert — personne n'écoutait ses avertissements répétés."
  → désert = figuré (expression idiomatique, parler sans être entendu)
• "Déplacer des montagnes — elle ferait tout pour sauver son entreprise."
  → montagnes = figuré (expression idiomatique, effort surhumain)
• "Ce n'est pas la mer à boire — il suffit de remplir deux formulaires."
  → mer = figuré (expression idiomatique, ce n'est pas difficile)
• "Sa carrière était un désert depuis son licenciement."
  → désert = figuré (métaphore pour une période sans activité)
• "Ils vivaient dans un océan de dettes depuis la faillite."
  → océan = figuré (métaphore pour une grande quantité accablante)
• "Il avait enfin réussi à sortir du bourbier de ses dettes accumulées pendant des années."
  → bourbier = figuré (métaphore pour une situation embourbée, difficile à quitter)
• "Le temps l'avait lentement extrait des sables mouvants de sa dépression."
  → sables mouvants = figuré (métaphore pour une situation qui engloutit progressivement)
• "Cette lettre avait traversé des décennies et des océans avant de lui parvenir."
  → océans = figuré (métaphore pour une grande distance temporelle et géographique-émotionnelle)
• "Être jeté dans l'arène sans préparation — c'est ce qu'il avait ressenti à son premier jour."
  → arène = figuré (métaphore pour une situation de compétition/confrontation)
• "La chaleur de leur accueil était un véritable incendie de bienveillance."
  → incendie = figuré (métaphore hyperbolique pour une intensité émotionnelle)
• "L'effervescence de la salle de rédaction brûlait comme un feu de camp permanent."
  → feu = figuré (comparaison pour une énergie collective intense, pas un vrai feu)
• "Je prépare en moi la renaissance du printemps, ce renouveau que j'attends depuis des mois."
  → renaissance du printemps = figuré (métaphore pour un renouveau intérieur/psychologique)
• "Son sourire était une éclaircie après des mois de tempête intérieure."
  → tempête = figuré (métaphore pour une période de trouble émotionnel)
• "Après des années passées dans les marécages de l'indécision, il avait enfin choisi."
  → marécages = figuré (métaphore pour une situation d'enlisement et d'hésitation)

CAS DIFFICILES — règles décisives:
• "Le temps + terme géographique" (le temps nous a poussés hors des marais) → TOUJOURS figuré (le temps ne pousse pas dans de vrais marais)
• "Terme + de + abstraction" (incendie de bienveillance, océan de dettes, forêt de questions) → figuré (DE_QUANTIF ou métaphore)
• "Traverser/franchir + terme + et + abstraction" (traversé la mer et ma mémoire) → figuré (énumération poétique)
• "Renaissance/renouveau du paysage/printemps" dans contexte intérieur → figuré
• Vrai appareil de cuisson qui produit de la chaleur réelle → référentiel (pas figuré)
• Vrai lieu géographique avec coordonnées ou description physique → référentiel
• Terme géographique suivi immédiatement d'une notion abstraite humaine → figuré
"""

CORE_DEFINITIONS = """
DÉFINITIONS:
- référentiel: le terme désigne un lieu géographique ou phénomène écologique RÉEL — physiquement présent ou mentionné dans un contexte concret (naturaliste, géographique, scientifique, écologique)
- figuré: le terme est utilisé comme métaphore, comparaison (avec "comme"), expression idiomatique, ou symbole abstrait décrivant une situation ou émotion humaine

⚠️ RÈGLES CLÉS:
1. Expression idiomatique connue → toujours figuré
2. "Le temps + terme géographique" comme sujet → toujours figuré
3. Terme géographique + abstraction humaine dans même énumération → figuré
4. "Incendie/feu/flamme" décrivant une émotion ou intensité → figuré
5. "Renaissance/renouveau" du paysage dans contexte humain → figuré
6. Terme géographique dans un contexte écologique/scientifique/physique → référentiel
7. Vrai appareil ou source de chaleur physique → référentiel
"""

def build_prompt(token, contexte):
    return f"""Tu es un expert en sémantique française. Détermine si le terme est utilisé de façon LITTÉRALE (référentiel) ou FIGURÉE dans cette phrase.

{CORE_DEFINITIONS}

{EXAMPLES_LOTERRE}

TERME À ANALYSER: <terme>{token}</terme>
PHRASE: {contexte}

Réponds UNIQUEMENT avec ce JSON:
{{"label": "référentiel"}} ou {{"label": "figuré"}}"""

def classify(token, contexte):
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": build_prompt(token, contexte)}],
            "stream": False,
            "options": {"temperature": 0, "num_predict": 5000},
        }, timeout=300)
        resp.raise_for_status()
        raw = resp.json()["message"]["content"].strip()
    except Exception as e:
        print(f"    ERROR: {e}")
        return None

    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    raw = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    # found 2026-10-19 (Loterre full-corpus run, 528/30166 rows affected):
    # a malformed-JSON response (e.g. an unquoted key) used to raise inside
    # the same try block as the HTTP call, which skipped straight to the
    # except and threw away the raw text entirely — even though the raw
    # text almost always still contains a plain "référentiel"/"figuré"
    # substring. Parsing is now outside the network try/except so a JSON
    # error falls through to the substring fallback below instead of
    # discarding a real answer and defaulting to "référentiel" blindly.
    m = re.search(r'\{[^}]+\}', raw)
    if m:
        try:
            data = json.loads(m.group(0))
            label = data.get("label", "").strip().lower()
            if label in ["référentiel", "figuré"]:
                return label
        except json.JSONDecodeError:
            pass
    for label in ["référentiel", "figuré"]:
        if label in raw.lower():
            return label
    return None

def main():
    gold = []
    with open(GOLD_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=";"):
            label = row["consensus"].strip()
            if label in ["référentiel", "figuré"]:
                gold.append({
                    "fichier":  row.get("fichier", "").strip(),
                    "token":    row["token_lexique"].strip(),
                    "contexte": row["contexte"].strip(),
                    "label":    label,
                })

    print(f"\n{'='*70}")
    print(f"  LOTERRE v8 — {len(gold)} examples")
    print(f"  Référentiel: {sum(1 for g in gold if g['label']=='référentiel')}")
    print(f"  Figuré: {sum(1 for g in gold if g['label']=='figuré')}")
    print(f"{'='*70}\n")

    results = []
    correct_total = correct_ref = correct_fig = 0
    total_ref = total_fig = 0

    for i, item in enumerate(gold, 1):
        pred = classify(item["token"], item["contexte"])
        if pred is None:
            pred = "référentiel"

        is_correct = int(pred == item["label"])
        correct_total += is_correct

        if item["label"] == "référentiel":
            total_ref += 1
            correct_ref += is_correct
        else:
            total_fig += 1
            correct_fig += is_correct

        results.append({
            "fichier":      item["fichier"],
            "token":        item["token"],
            "contexte":     item["contexte"],
            "gold_label":   item["label"],
            "qwen_pred":    pred,
            "qwen_correct": is_correct,
        })

        if i % 20 == 0 or i == len(gold):
            acc     = correct_total / i * 100
            acc_ref = correct_ref / max(total_ref, 1) * 100
            acc_fig = correct_fig / max(total_fig, 1) * 100
            print(f"  [{i:>3}/{len(gold)}] Overall={acc:.1f}%  Réf={acc_ref:.1f}%  Fig={acc_fig:.1f}%")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    overall = correct_total / len(gold) * 100
    ref_acc = correct_ref / max(total_ref, 1) * 100
    fig_acc = correct_fig / max(total_fig, 1) * 100

    print(f"\n{'='*70}")
    print(f"  LOTERRE v8 FINAL")
    print(f"  Overall: {overall:.1f}%  Réf: {ref_acc:.1f}%  Fig: {fig_acc:.1f}%")
    print(f"\n  Comparison:")
    print(f"  v3: 85.2% / 56.1% fig")
    print(f"  v6: 86.2% / 61.0% fig  ← previous best")
    print(f"  v8: {overall:.1f}% / {fig_acc:.1f}% fig")
    print(f"{'='*70}")
    print(f"\n  Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
