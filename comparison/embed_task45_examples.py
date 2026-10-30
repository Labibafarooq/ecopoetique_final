import csv, json, torch
from transformers import AutoTokenizer, AutoModel

MODEL_NAME = "intfloat/multilingual-e5-base"

print("loading embedding model (CPU, one-time)...")
tok = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.eval()

def embed(texts):
    texts = [f"query: {t}" for t in texts]
    batch = tok(texts, padding=True, truncation=True, max_length=256, return_tensors="pt")
    with torch.no_grad():
        out = model(**batch)
    emb = out.last_hidden_state
    mask = batch["attention_mask"].unsqueeze(-1).float()
    pooled = (emb * mask).sum(1) / mask.sum(1)
    pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
    return pooled.numpy()

def is_x(v):
    return v.strip().lower() == "x"

with open("/raid/home/farooq/projects/ecopoetique_v2/métaphore/gold_task2_task45_CURRENT.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter=";"))

usable = []
for r in rows:
    if is_x(r.get("subcategorie_metaphore","")) or is_x(r.get("categorie_compare","")) or is_x(r.get("notes","")):
        continue
    gc = r.get("categorie_compare","").strip()
    if gc == "?" or not gc:
        continue
    usable.append(r)

print(f"usable rows: {len(usable)}")
texts = [f"{r['token_lexique'].strip()} | {r['contexte'].strip()}" for r in usable]
embeddings = embed(texts)
print("embeddings shape:", embeddings.shape)

import numpy as np
np.save("task45_embeddings.npy", embeddings)
with open("task45_embeddings_meta.json", "w") as f:
    json.dump([{"id": r["id"], "token": r["token_lexique"].strip(), "gold": r["categorie_compare"].strip().upper()} for r in usable], f)
print("saved task45_embeddings.npy + task45_embeddings_meta.json")
