"""
run_task1_corpus.py  --category animaux|plantes

Task 1: classify each animal/plant mention as référentiel or figuré.
  - Model  : qwen3:30b  on http://localhost:11434 (corrected 2026-10-12 for the new DGX server)
  - Batch  : 4 rows per API call
  - Prompts: exact v6 prompts (same as evaluate_all_goldsets_v6.py)
  - Input  : corpus_principal + bestsellers merged
  - Output : ../resultats/task1_<category>_labels.csv
  - Resume : re-running picks up where it left off

Usage:
  python3 run_task1_corpus.py --category animaux
  python3 run_task1_corpus.py --category plantes
"""

import argparse, csv, json, os, re, requests, time

# ── Config ────────────────────────────────────────────────────────────────────

OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3:30b"
BATCH_SIZE   = 4
SAVE_EVERY   = 200   # flush output to disk every N rows

# ── GPU throttling ───────────────────────────────────────────────────────────
# 2026-07-06: added to reduce time-averaged GPU compute utilization (not memory —
# VRAM usage is unaffected, the model stays loaded the whole time) so a colleague
# can share the same physical GPU. After each batch call, sleeps for
# THROTTLE_SLEEP_RATIO x the call's own duration, creating real idle windows.
# THROTTLE_SLEEP_RATIO=1.0 -> ~50% duty cycle (idle time == active time).
# This roughly DOUBLES total wall-clock runtime for the same amount of work —
# it's a real trade, not a free lunch. No root/MPS available on this machine,
# so this is the best available lever (see project memory for why num_gpu/MIG/
# MPS don't fit: memory isn't the constraint here, only compute utilization is).
THROTTLE_ENABLED    = True
THROTTLE_SLEEP_RATIO = 1.0

CORPUS_FILES = {
    "animaux": [
        ("../resultats/corpus_principal/ENTITES_contexte_animaux.csv",  "\t", "truncated_sentence"),
        ("../resultats/bestsellers/BESTSELLERS_contexte_animaux.csv",   "\t", "contexte"),
    ],
    "plantes": [
        ("../resultats/corpus_principal/ENTITES_contexte_plantes.csv",  "\t", "truncated_sentence"),
        ("../resultats/bestsellers/BESTSELLERS_contexte_plantes.csv",   "\t", "contexte"),
    ],
}

OUTPUT_DIR = "../resultats"

# ── Exact v6 prompts ──────────────────────────────────────────────────────────

EXAMPLES = {
    "animaux": """
EXEMPLES — termes animaux (indépendants du jeu d'évaluation):

référentiel (animal réel):
• "Le fermier nourrissait ses poules chaque matin avant le lever du soleil."
  → poules = référentiel (vraies volailles d'élevage)
• "Un aigle tournoyait lentement au-dessus des rochers calcaires."
  → aigle = référentiel (oiseau réel observé dans la nature)
• "La rivière grouillait de truites que les pêcheurs tentaient d'attraper."
  → truites = référentiel (poissons réels dans une rivière)
• "Elle tira le chat par la queue pour le faire descendre de la table."
  → chat = référentiel (animal domestique présent physiquement)

figuré (métaphore, comparaison, expression):
• "Monter sur ses grands chevaux — il s'est mis en colère pour rien."
  → chevaux = figuré (expression idiomatique, pas de vrais chevaux)
• "Elle avait un caractère de cochon — personne ne pouvait la supporter."
  → cochon = figuré (expression pour décrire le caractère d'une personne)
• "Il travaillait comme un bœuf du matin au soir sans jamais se plaindre."
  → bœuf = figuré (comparaison pour décrire l'effort humain)
• "Avoir d'autres chats à fouetter — j'ai des choses plus importantes à faire."
  → chats = figuré (expression idiomatique française)
• "Les candidats tombaient comme des mouches face aux questions du jury."
  → mouches = figuré (comparaison, pas de vraies mouches)""",

    "plantes": """
EXEMPLES — termes végétaux/plantes:

référentiel (plante réelle):
• "Le jardinier arrosait ses tomates chaque soir en été."
  → tomates = référentiel (vraies plantes dans un jardin)
• "La forêt de chênes centenaires longeait toute la route départementale."
  → chênes = référentiel (vrais arbres dans un paysage)
• "Elle cueillit des champignons dans le sous-bois humide de novembre."
  → champignons = référentiel (vrais champignons cueillis)
• "Les vignes de Bourgogne produisent certains des meilleurs vins du monde."
  → vignes = référentiel (vraies plantes viticoles)
• "L'olivier millénaire se dressait au centre de la place du village."
  → olivier = référentiel (vrai arbre présent physiquement)

figuré (métaphore, expression idiomatique):
• "Les carottes sont cuites — il est trop tard pour changer quoi que ce soit."
  → carottes = figuré (expression figée)
• "Mettre du beurre dans les épinards — il cherchait à améliorer ses revenus."
  → épinards = figuré (expression idiomatique)
• "Ne pas avoir un radis — il était complètement fauché après les vacances."
  → radis = figuré (expression idiomatique)
• "Elle était fleur bleue — elle croyait encore aux contes de fées à trente ans."
  → fleur = figuré (expression pour désigner quelqu'un de romantique naïf)
• "Sa chevelure était une forêt sombre où l'on pouvait se perdre facilement."
  → forêt = figuré (métaphore pour des cheveux très épais)

CAS DIFFICILES:
• "La branche d'olivier symbolisait la paix dans les négociations." → olivier = figuré (symbole)
• "Ne laissez pas la branche d'olivier tomber de ma main…" → olivier = figuré (symbole politique/religieux)
• "L'agriculteur taille ses oliviers chaque printemps." → oliviers = référentiel (vrais arbres)
• "Elle a la peau couleur lime." → lime = figuré (comparaison de couleur, pas de vraie lime)""",
}

CORE_DEFINITIONS = """
DÉFINITIONS:
- référentiel: le terme désigne un être vivant, lieu, ou élément naturel RÉEL — physiquement présent ou mentionné comme tel dans un contexte concret (naturaliste, géographique, culinaire, scientifique, écologique)
- figuré: le terme est utilisé comme métaphore, comparaison (avec "comme"), expression idiomatique figée, personnification, ou symbole abstrait décrivant une situation ou émotion humaine

⚠️ RÈGLES CLÉS:
1. Expression idiomatique connue (carottes cuites, mer à boire, montagnes à déplacer...) → toujours figuré
2. Terme dans une comparaison avec "comme" pour décrire un humain → figuré
3. Terme décrivant un lieu ou être réellement présent dans la scène → référentiel
4. Terme dans un contexte scientifique, géographique, naturaliste, écologique → référentiel
5. Crise environnementale réelle (réchauffement, pollution, extinction) → référentiel même si le verbe semble fort
6. Terme géographique africain/asiatique dans contexte colonial ou de voyage → référentiel
7. Terme dans une métaphore décrivant émotion ou situation humaine → figuré
"""

def build_batch_prompt(items, category):
    entries = "\n".join(
        f'{i}. TERME: <terme>{token}</terme> | PHRASE: {contexte}'
        for i, token, contexte in items
    )
    return (
        "Tu es un expert en sémantique française. Pour chaque entrée numérotée, "
        "détermine si le terme est utilisé de façon LITTÉRALE (référentiel) ou FIGURÉE.\n\n"
        + CORE_DEFINITIONS + "\n"
        + EXAMPLES[category] + "\n\n"
        + "ENTRÉES À CLASSIFIER:\n"
        + entries + "\n\n"
        + "Réponds UNIQUEMENT avec ce JSON (respecte l'ordre et les numéros):\n"
        + '[{"id": 1, "label": "..."}, {"id": 2, "label": "..."}, ...]'
    )

def call_ollama(prompt):
    resp = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 5000},
    }, timeout=300)
    raw = resp.json()["message"]["content"].strip()
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

def parse_batch(raw, n):
    results = {}
    arr_match = re.search(r'\[.*?\]', raw, re.DOTALL)
    if arr_match:
        try:
            arr = json.loads(arr_match.group(0))
            for item in arr:
                item_id = item.get("id")
                label = item.get("label", "").strip().lower()
                if item_id and label in ["référentiel", "figuré"]:
                    results[item_id] = label
            if len(results) == n:
                return results
        except: pass
    for m in re.finditer(r'\{[^}]+\}', raw):
        try:
            obj = json.loads(m.group(0))
            item_id = obj.get("id")
            label = obj.get("label", "").strip().lower()
            if item_id and label in ["référentiel", "figuré"]:
                results[item_id] = label
        except: pass
    return results

# ── Load corpus ───────────────────────────────────────────────────────────────

def load_corpus(category):
    """Load and merge corpus_principal + bestsellers. Normalize context column to 'contexte'."""
    rows = []
    for fpath, sep, ctx_col in CORPUS_FILES[category]:
        if not os.path.exists(fpath):
            print(f"  WARNING: {fpath} not found, skipping.")
            continue
        csv.field_size_limit(10**7)
        with open(fpath, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=sep)
            for row in reader:
                # normalize context column name
                contexte = row.get(ctx_col, row.get("contexte", row.get("truncated_sentence", ""))).strip()
                rows.append({
                    "fichier":       row.get("fichier", "").strip(),
                    "token_lexique": row.get("token_lexique", "").strip(),
                    "contexte":      contexte,
                    "lemme":         row.get("lemme", "").strip(),
                    "categorie":     row.get("categorie", "").strip(),
                })
        print(f"  Loaded {fpath}: {len(rows)} rows so far")
    return rows

def dedup_rows(rows):
    """Deduplicate by (fichier, token_lexique, contexte). Returns unique rows + mapping."""
    seen = {}
    unique = []
    dup_map = {}  # index in rows → index in unique
    for i, row in enumerate(rows):
        key = (row["fichier"], row["token_lexique"], row["contexte"])
        if key not in seen:
            seen[key] = len(unique)
            unique.append(row)
        dup_map[i] = seen[key]
    return unique, dup_map

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=["animaux", "plantes"], required=True)
    args = parser.parse_args()
    category = args.category

    output_path = os.path.join(OUTPUT_DIR, f"task1_{category}_labels.csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\nTask 1 corpus run — {category.upper()}")
    print(f"Model  : {OLLAMA_MODEL}")
    print(f"Batch  : {BATCH_SIZE}")
    print(f"Output : {output_path}")
    print("=" * 65)

    # Load all rows
    print("\nLoading corpus...")
    all_rows = load_corpus(category)
    print(f"Total rows (before dedup): {len(all_rows):,}")

    unique_rows, dup_map = dedup_rows(all_rows)
    print(f"Unique rows (after dedup): {len(unique_rows):,}")
    print(f"Duplicate rows skipped  : {len(all_rows) - len(unique_rows):,}")

    # Load already-done labels from output file (resume)
    done_labels = {}  # unique_index → label
    if os.path.exists(output_path):
        csv.field_size_limit(10**7)
        with open(output_path, encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                key = (row.get("fichier",""), row.get("token_lexique",""), row.get("contexte",""))
                label = row.get("task1_label", "")
                if label in ["référentiel", "figuré"]:
                    # find index in unique_rows
                    for idx, r in enumerate(unique_rows):
                        if (r["fichier"], r["token_lexique"], r["contexte"]) == key:
                            done_labels[idx] = label
                            break
        print(f"Resuming: {len(done_labels):,} rows already done")

    remaining = [i for i in range(len(unique_rows)) if i not in done_labels]
    print(f"Rows to classify: {len(remaining):,}")

    if not remaining:
        print("All rows already classified!")
    else:
        base_speed = 3.9 * (1 + THROTTLE_SLEEP_RATIO) if THROTTLE_ENABLED else 3.9
        est_h = len(remaining) * base_speed / 3600
        throttle_note = f" (throttled: ~{100/(1+THROTTLE_SLEEP_RATIO):.0f}% GPU duty cycle)" if THROTTLE_ENABLED else ""
        print(f"Estimated time: {est_h:.0f}h ({est_h/24:.1f} days at {base_speed:.1f}s/row){throttle_note}")

    # Warmup
    print("\nWarming up model...", flush=True)
    requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": "bonjour"}],
        "stream": False, "options": {"num_predict": 5},
    }, timeout=60)
    print("Done.\n")

    # Open output file for appending
    file_exists = os.path.exists(output_path)
    out_f = open(output_path, "a", encoding="utf-8", newline="")
    writer = csv.DictWriter(out_f, fieldnames=["fichier","token_lexique","contexte","lemme","categorie","task1_label"], delimiter="\t")
    if not file_exists or os.path.getsize(output_path) == 0:
        writer.writeheader()

    # Track rows that got a default label due to batch parse failure
    failed_keys_path = os.path.join(OUTPUT_DIR, f"task1_{category}_failed_keys.tsv")
    failed_keys_f = open(failed_keys_path, "a", encoding="utf-8", newline="")
    failed_keys_writer = csv.writer(failed_keys_f, delimiter="\t")
    if not os.path.exists(failed_keys_path) or os.path.getsize(failed_keys_path) == 0:
        failed_keys_writer.writerow(["fichier", "token_lexique", "contexte"])

    # Classify
    times = []
    total_sleep = 0.0
    failed = 0
    written = 0
    start_all = time.time()

    i = 0
    while i < len(remaining):
        chunk_indices = remaining[i:i + BATCH_SIZE]
        chunk = [unique_rows[idx] for idx in chunk_indices]
        items = [(j+1, r["token_lexique"], r["contexte"]) for j, r in enumerate(chunk)]

        t0 = time.time()
        try:
            raw = call_ollama(build_batch_prompt(items, category))
            preds = parse_batch(raw, len(chunk))
        except Exception as e:
            print(f"  ERROR at row {i}: {e} — retrying once...")
            time.sleep(5)
            try:
                raw = call_ollama(build_batch_prompt(items, category))
                preds = parse_batch(raw, len(chunk))
            except:
                preds = {}
        elapsed = time.time() - t0
        times.append(elapsed)

        if THROTTLE_ENABLED:
            sleep_time = elapsed * THROTTLE_SLEEP_RATIO
            total_sleep += sleep_time
            time.sleep(sleep_time)

        if len(preds) < len(chunk):
            failed += 1

        for j, (idx, row) in enumerate(zip(chunk_indices, chunk)):
            label = preds.get(j+1)
            if label is None:
                # batch parse failed for this row — log it for recovery, default to référentiel
                label = "référentiel"
                failed_keys_writer.writerow([row["fichier"], row["token_lexique"], row["contexte"]])
                failed_keys_f.flush()
            done_labels[idx] = label
            writer.writerow({
                "fichier":      row["fichier"],
                "token_lexique":row["token_lexique"],
                "contexte":     row["contexte"],
                "lemme":        row["lemme"],
                "categorie":    row["categorie"],
                "task1_label":  label,
            })
            written += 1

        i += BATCH_SIZE

        # Progress every 100 rows
        if written % 100 == 0 or i >= len(remaining):
            out_f.flush()
            compute_per_row = sum(times) / len(times) / BATCH_SIZE
            # wall_per_row includes the throttle sleep, so ETA reflects real
            # (slower) completion time, not just GPU-busy time.
            wall_per_row = (sum(times) + total_sleep) / len(times) / BATCH_SIZE
            avg_per_row = wall_per_row
            done_count  = len(done_labels)
            total_u     = len(unique_rows)
            pct         = done_count / total_u * 100
            remaining_rows = total_u - done_count
            eta_h = remaining_rows * wall_per_row / 3600
            elapsed_h = (time.time() - start_all) / 3600
            ref_count = sum(1 for l in done_labels.values() if l == "référentiel")
            fig_count = sum(1 for l in done_labels.values() if l == "figuré")
            print(
                f"  [{done_count:>7,}/{total_u:,}] {pct:5.1f}%  "
                f"réf={ref_count:,} fig={fig_count:,}  "
                f"wall_speed={wall_per_row:.1f}s/row (gpu_compute={compute_per_row:.1f}s/row)  "
                f"ETA={eta_h:.1f}h  elapsed={elapsed_h:.1f}h  "
                f"failed_batches={failed}",
                flush=True
            )

    out_f.close()
    failed_keys_f.close()
    print(f"Failed keys log: {failed_keys_path}")

    # Write FULL output (all rows including duplicates) with labels
    full_output_path = os.path.join(OUTPUT_DIR, f"task1_{category}_labels_full.csv")
    print(f"\nWriting full output (with duplicates) → {full_output_path}")
    with open(full_output_path, "w", encoding="utf-8", newline="") as f:
        writer2 = csv.DictWriter(f, fieldnames=["fichier","token_lexique","contexte","lemme","categorie","task1_label"], delimiter="\t")
        writer2.writeheader()
        for i, row in enumerate(all_rows):
            unique_idx = dup_map[i]
            label = done_labels.get(unique_idx, "référentiel")
            writer2.writerow({
                "fichier":      row["fichier"],
                "token_lexique":row["token_lexique"],
                "contexte":     row["contexte"],
                "lemme":        row["lemme"],
                "categorie":    row["categorie"],
                "task1_label":  label,
            })

    total_h = (time.time() - start_all) / 3600
    print(f"\nDone! Total time: {total_h:.1f}h")
    print(f"Output (unique): {output_path}")
    print(f"Output (full)  : {full_output_path}")
    ref_total = sum(1 for l in done_labels.values() if l == "référentiel")
    fig_total = sum(1 for l in done_labels.values() if l == "figuré")
    print(f"Results: {ref_total:,} référentiel  |  {fig_total:,} figuré  ({fig_total/(ref_total+fig_total)*100:.1f}% figuré)")

if __name__ == "__main__":
    main()
