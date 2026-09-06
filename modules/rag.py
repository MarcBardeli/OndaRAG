import os
import glob
import re
from typing import List

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
except Exception:
    np = None
    SentenceTransformer = None

# Lightweight embedding model 
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800

DOCUMENTS: List[dict] = []
_EMBED_MODEL = None


def _split_text(text, size=CHUNK_SIZE):

    parts = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    chunks = []

    for p in parts:

        if len(p) <= size:

            chunks.append(p)

        else:

            start = 0
            while start < len(p):
                chunks.append(p[start:start+size].strip())
                start += size

    return chunks


def _init_model():

    global _EMBED_MODEL

    if _EMBED_MODEL is None and SentenceTransformer is not None:

        try:

            _EMBED_MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)

        except Exception:

            _EMBED_MODEL = None


def load_documents(knowledge_dir="knowledge"):

    global DOCUMENTS

    DOCUMENTS = []

    if not os.path.exists(knowledge_dir):
        os.makedirs(knowledge_dir, exist_ok=True)

    patterns = ["**/*.txt", "**/*.md"]

    all_chunks = []

    for pattern in patterns:

        for path in glob.glob(os.path.join(knowledge_dir, pattern), recursive=True):

            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                continue

            chunks = _split_text(text)

            for i, c in enumerate(chunks):

                doc = {
                    "source": os.path.basename(path),
                    "content": c,
                    "id": f"{os.path.basename(path)}::{i}",
                    "embedding": None,
                }

                DOCUMENTS.append(doc)
                all_chunks.append(c)

    # compute embeddings if model is available
    _init_model()

    if _EMBED_MODEL is not None and DOCUMENTS:

        try:
            embeddings = _EMBED_MODEL.encode(
                [d["content"] for d in DOCUMENTS],
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            for d, emb in zip(DOCUMENTS, embeddings):
                d["embedding"] = emb

        except Exception:
            # leave embeddings as None
            pass


def reindex(knowledge_dir="knowledge"):

    load_documents(knowledge_dir)


def _cosine_sim(a, b):

    if a is None or b is None:
        return 0.0

    num = float(np.dot(a, b))
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return num / denom


def _score_basic(query, text):
    q_tokens = set(re.findall(r"\w+", query.lower()))
    t_tokens = re.findall(r"\w+", text.lower())
    if not q_tokens or not t_tokens:
        return 0
    overlap = q_tokens.intersection(set(t_tokens))
    return len(overlap) / max(1, len(q_tokens))


def retrieve(query, top_k=3):

    # ensure docs loaded
    if not DOCUMENTS:
        load_documents()

    results = []

    # prefer embedding-based retrieval
    if _EMBED_MODEL is not None and np is not None:

        try:
            q_emb = _EMBED_MODEL.encode([query], convert_to_numpy=True)[0]

            sims = []

            for d in DOCUMENTS:

                score = _cosine_sim(q_emb, d.get("embedding"))

                sims.append((score, d))

            sims.sort(key=lambda x: x[0], reverse=True)

            for s, d in sims[:top_k]:

                if s > 0:
                    results.append({"source": d["source"], "content": d["content"], "score": float(s)})

            return results

        except Exception:

            # fallback to basic
            pass

    # fallback simple scoring
    scored = []
    for doc in DOCUMENTS:
        score = _score_basic(query, doc["content"]) * 1.0
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    for s, d in scored[:top_k]:
        results.append({"source": d["source"], "content": d["content"], "score": float(s)})

    return results


# load at import time
load_documents()
