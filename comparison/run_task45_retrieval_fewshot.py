import csv, json, os, re, requests
import numpy as np

OLLAMA_URL = "http://127.0.0.1:11436/api/chat"
MODEL = "qwen3:30b"
TIMEOUT = 300

CATEGORIES = {
    "CH": "Corps humain et processus biologiques",
    "P":  "États psychologiques et fonctions cognitives (émotions, sensations, mémoire, imagination)",
    "NH": "Créatures non humaines vivantes et processus biologiques (animaux, plantes, en tant qu'elles-mêmes)",
    "O":  "Objets et structures artificiels (fabriqués par l'homme)",
    "E":  "Éléments naturels inanimés et processus naturels (paysages, météo, géologie)",
    "A":  "Concepts abstraits (politique, religion, art, institutions sociales)",
}
VALID_CODES = list(CATEGORIES.keys())

with open(os.path.join(os.path.dirname(__file__), "task45_embeddings_meta.json")) as f:
    META = json.load(f)
EMBEDDINGS = np.load(os.path.join(os.path.dirname(__file__), "task45_embeddings.npy"))
ID_TO_IDX = {m["id"]: i for i, m in enumerate(META)}

with open(os.path.expanduser("~/ecopoetique/métaphore/gold_task2_task45_CURRENT.csv"), encoding="utf-8") as f:
    GOLD_ROWS = {r["id"]: r for r in csv.DictReader(f, delimiter=";")}

def retrieve_examples(query_id, pool_ids, k=6):
    """Return the k most similar examples to query_id, drawn only from pool_ids
    (never query_id itself), for use as few-shot examples. Caller controls
    pool_ids to enforce leave-one-out / dev-only retrieval as needed."""
    q_idx = ID_TO_IDX[query_id]
    q_vec = EMBEDDINGS[q_idx]
    pool_idx = [ID_TO_IDX[pid] for pid in pool_ids if pid != query_id and pid in ID_TO_IDX]
    sims = EMBEDDINGS[pool_idx] @ q_vec
    order = np.argsort(-sims)[:k]
    return [META[pool_idx[i]] for i in order]

def make_prompt(token, context, subcategory, examples):
    cats_desc = "\n".join(f"  {code}: {desc}" for code, desc in CATEGORIES.items())
    ex_block = ""
    for ex in examples:
        er = GOLD_ROWS[ex["id"]]
        ex_block += (f'- «{ex["token"]}» dans «{er["contexte"].strip()[:200]}» '
                     f'→ cible = {ex["gold"]}\n')
    return f"""Tu es expert en stylistique française, formé à la théorie de la métaphore
conceptuelle (véhicule / cible). Classe la CIBLE (le référent réel comparé au
véhicule) selon le type d'entité qu'elle EST littéralement — jamais selon le
domaine de la qualité illustrée.

Catégories:
{cats_desc}

EXEMPLES RÉELS les plus similaires à ce cas précis (utilise-les comme guide
pour calibrer ta décision, surtout pour les cas ambigus CH/A/P) :
{ex_block}
Nouveau cas à classer :
Le mot «{token}» (figure: {subcategory}) est utilisé de façon figurative dans :
«{context}»

Identifie la cible réelle, puis classe-la. Réponds UNIQUEMENT en JSON :
{{"cible": "...", "code": "CODE"}}"""

def call_ollama(prompt):
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0, "num_predict": 4000, "num_ctx": 16384},
        }, timeout=TIMEOUT)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        m = re.search(r'\{.*?\}', content, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            code = data.get("code", "").strip().upper()
            if code in VALID_CODES:
                return code, data.get("cible", "")
        for code in VALID_CODES:
            if code in content:
                return code, ""
        return "UNKNOWN", content[:100]
    except requests.exceptions.Timeout:
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL, "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0, "num_predict": 4000, "num_ctx": 16384},
            }, timeout=TIMEOUT)
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            m = re.search(r'\{.*?\}', content, re.DOTALL)
            if m:
                data = json.loads(m.group(0))
                code = data.get("code", "").strip().upper()
                if code in VALID_CODES:
                    return code, data.get("cible", "")
            return "ERROR", "retry also failed to parse"
        except Exception as e:
            return "ERROR", str(e)[:80]
    except Exception as e:
        return "ERROR", str(e)[:80]
