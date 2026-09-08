import os
import glob
import re
import pickle
from typing import List

try:
    import numpy as np
except Exception:
    np = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

try:
    import faiss
except Exception:
    faiss = None

try:
    import torch
except Exception:
    torch = None


EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

SEMANTIC_CANDIDATES = 20
LEXICAL_CANDIDATES = 20
DEFAULT_TOP_K = 3
SEMANTIC_WEIGHT = 0.75
LEXICAL_WEIGHT = 0.25
MIN_SEMANTIC_SCORE = 0.20

# FAISS index
INDEX_DIR = ".rag_index"

FAISS_INDEX_FILE = os.path.join(INDEX_DIR, "index.faiss")
DOCUMENTS_FILE = os.path.join(INDEX_DIR, "documents.pkl")


DOCUMENTS: List[dict] = []

_EMBED_MODEL = None
_FAISS_INDEX = None


def _split_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Divides a document into chunks trying to respect paragraphs.

    If a chunk is too big, it is split into pieces with overlap.
    """

    if not text:
        return []

    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()

    if not text:
        return []

    paragraphs = [
        p.strip()
        for p in re.split(r"\n{2,}", text)
        if p.strip()
    ]

    chunks = []
    current = ""

    for paragraph in paragraphs:

        # If chunk is small enough, we can add it
        if len(paragraph) <= size:

            if not current:
                current = paragraph

            elif len(current) + 2 + len(paragraph) <= size:
                current += "\n\n" + paragraph

            else:
                chunks.append(current.strip())

                # Overlap whit previous chunk
                overlap_text = current[-overlap:].strip()

                if overlap_text:
                    current = overlap_text + "\n\n" + paragraph
                else:
                    current = paragraph

        else:
            # If a chunk is too big it is split into pieces
            if current:
                chunks.append(current.strip())
                current = ""

            start = 0

            while start < len(paragraph):

                end = start + size
                piece = paragraph[start:end].strip()

                if piece:
                    chunks.append(piece)

                # Evitamos avanzar menos que el overlap
                step = max(1, size - overlap)
                start += step

    if current:
        chunks.append(current.strip())

    return [c for c in chunks if c]

def _init_model():

    global _EMBED_MODEL

    if _EMBED_MODEL is None and SentenceTransformer is not None:

        try:

            device = "cpu"

            if torch is not None and torch.cuda.is_available():
                device = "cuda"

            print(f"[RAG] Loading embedding model on: {device}")

            _EMBED_MODEL = SentenceTransformer(
                EMBEDDING_MODEL_NAME,
                device=device
            )

        except Exception as e:

            print(f"[RAG] Could not load embedding model: {e}")

            _EMBED_MODEL = None


def load_documents(knowledge_dir="knowledge"):
    """
    Loads documents from knowledge_dir.
    """

    global DOCUMENTS
    global _FAISS_INDEX

    DOCUMENTS = []
    _FAISS_INDEX = None

    if not os.path.exists(knowledge_dir):
        os.makedirs(knowledge_dir, exist_ok=True)

    patterns = [
        "**/*.txt",
        "**/*.md",
    ]

    for pattern in patterns:

        for path in glob.glob(
            os.path.join(knowledge_dir, pattern),
            recursive=True
        ):

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as f:
                    text = f.read()

            except Exception:
                continue

            chunks = _split_text(text)

            for i, content in enumerate(chunks):


                try:
                    source = os.path.relpath(
                        path,
                        knowledge_dir
                    )
                except Exception:
                    source = os.path.basename(path)

                doc = {
                    "source": source,
                    "content": content,
                    "id": f"{source}::{i}",
                    "chunk_id": i,
                    "embedding": None,
                }

                DOCUMENTS.append(doc)

    _init_model()

    if (
        _EMBED_MODEL is not None
        and np is not None
        and DOCUMENTS
    ):
        _build_faiss_index()



def _build_faiss_index():
    """
    Generates embeddings and builds the FAISS index.
    """

    global _FAISS_INDEX
    global DOCUMENTS

    if (
        _EMBED_MODEL is None
        or np is None
        or not DOCUMENTS
    ):
        return

    try:

        texts = [
            d["content"]
            for d in DOCUMENTS
        ]

        embeddings = _EMBED_MODEL.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        faiss.normalize_L2(embeddings)

        for doc, emb in zip(
            DOCUMENTS,
            embeddings
        ):
            doc["embedding"] = emb

        dimension = embeddings.shape[1]

        if faiss is not None:

            index = faiss.IndexFlatIP(dimension)

            index.add(embeddings)

            _FAISS_INDEX = index

        else:
            _FAISS_INDEX = None

    except Exception:
        _FAISS_INDEX = None




def reindex(knowledge_dir="knowledge"):
    """
    Reconstructs the index.
    """

    load_documents(knowledge_dir)

    save_index()



def save_index():
    """
    Saves the FAISS index and documents to disk.
    """

    if not DOCUMENTS:
        return

    try:

        os.makedirs(
            INDEX_DIR,
            exist_ok=True
        )

        if (
            faiss is not None
            and _FAISS_INDEX is not None
        ):
            faiss.write_index(
                _FAISS_INDEX,
                FAISS_INDEX_FILE
            )

        with open(
            DOCUMENTS_FILE,
            "wb"
        ) as f:

            pickle.dump(
                DOCUMENTS,
                f
            )

    except Exception:
        pass


def load_index():
    """
    Tries to load a previously saved index.
    """

    global DOCUMENTS
    global _FAISS_INDEX

    if not os.path.exists(DOCUMENTS_FILE):
        return False

    try:

        with open(
            DOCUMENTS_FILE,
            "rb"
        ) as f:

            documents = pickle.load(f)

        if not documents:
            return False

        index = None

        if (
            faiss is not None
            and os.path.exists(FAISS_INDEX_FILE)
        ):

            index = faiss.read_index(
                FAISS_INDEX_FILE
            )

        DOCUMENTS = documents
        _FAISS_INDEX = index

        return True

    except Exception:

        DOCUMENTS = []
        _FAISS_INDEX = None

        return False



def _cosine_sim(a, b):

    if (
        a is None
        or b is None
        or np is None
    ):
        return 0.0

    try:

        num = float(
            np.dot(a, b)
        )

        denom = float(
            np.linalg.norm(a)
            * np.linalg.norm(b)
        )

        if denom == 0:
            return 0.0

        return num / denom

    except Exception:
        return 0.0




def _tokenize(text):
    """
    Simple tokenization.
    """

    if not text:
        return []

    return re.findall(
        r"\w+",
        text.lower(),
        flags=re.UNICODE
    )


def _score_basic(query, text):
    """
    Lexical score.
    """

    q_tokens = _tokenize(query)
    t_tokens = _tokenize(text)

    if not q_tokens or not t_tokens:
        return 0.0

    q_set = set(q_tokens)
    t_set = set(t_tokens)

    overlap = q_set.intersection(t_set)

    if not overlap:
        return 0.0

    coverage = len(overlap) / len(q_set)

    # Bonus if exact coincidence
    query_normalized = " ".join(q_tokens)
    text_normalized = " ".join(t_tokens)

    phrase_bonus = 0.0

    if query_normalized in text_normalized:
        phrase_bonus = 0.30

    frequency_score = 0.0

    for token in overlap:

        count = t_tokens.count(token)

        if count > 0:
            frequency_score += min(
                count,
                3
            ) * 0.02

    score = (
        coverage * 0.75
        + phrase_bonus
        + frequency_score
    )

    return min(
        1.0,
        score
    )


def _semantic_search(query, k=SEMANTIC_CANDIDATES):
    """
    Search for semantic candidates using FAISS.

    If FAISS is not available, use cosine similarity
    directly as a fallback.
    """

    if (
        _EMBED_MODEL is None
        or np is None
        or not DOCUMENTS
    ):
        return []

    try:

        q_emb = _EMBED_MODEL.encode(
            [query],
            convert_to_numpy=True
        )[0]

        q_emb = np.asarray(
            q_emb,
            dtype="float32"
        )

        q_norm = np.linalg.norm(q_emb)

        if q_norm == 0:
            return []

        q_emb = q_emb / q_norm


        if (
            faiss is not None
            and _FAISS_INDEX is not None
        ):

            search_k = min(
                k,
                len(DOCUMENTS)
            )

            scores, indices = _FAISS_INDEX.search(
                np.array(
                    [q_emb],
                    dtype="float32"
                ),
                search_k
            )

            results = []

            for score, index in zip(
                scores[0],
                indices[0]
            ):

                if index < 0:
                    continue

                doc = DOCUMENTS[index]

                score = float(score)

                if score >= MIN_SEMANTIC_SCORE:

                    results.append({
                        "source": doc["source"],
                        "content": doc["content"],
                        "score": score,
                        "semantic_score": score,
                        "lexical_score": 0.0,
                        "id": doc["id"],
                    })

            return results

        # Fallback without FAISS

        scored = []

        for doc in DOCUMENTS:

            score = _cosine_sim(
                q_emb,
                doc.get("embedding")
            )

            if score >= MIN_SEMANTIC_SCORE:

                scored.append(
                    (score, doc)
                )

        scored.sort(
            key=lambda x: x[0],
            reverse=True
        )

        results = []

        for score, doc in scored[:k]:

            results.append({
                "source": doc["source"],
                "content": doc["content"],
                "score": float(score),
                "semantic_score": float(score),
                "lexical_score": 0.0,
                "id": doc["id"],
            })

        return results

    except Exception:

        return []


def _lexical_search(
    query,
    k=LEXICAL_CANDIDATES
):
    """
    Simple lexical search.
    """

    scored = []

    for doc in DOCUMENTS:

        score = _score_basic(
            query,
            doc["content"]
        )

        if score > 0:

            scored.append(
                (score, doc)
            )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    results = []

    for score, doc in scored[:k]:

        results.append({
            "source": doc["source"],
            "content": doc["content"],
            "score": float(score),
            "semantic_score": 0.0,
            "lexical_score": float(score),
            "id": doc["id"],
        })

    return results


def retrieve(query, top_k=DEFAULT_TOP_K):
    """
    Hybrid retrieval.

    Combines:
        1. Semantic search
        2. Lexical search
        3. Deduplication
        4. Combined score
    """

    if not query or not query.strip():
        return []


    if not DOCUMENTS:

        loaded = load_index()

        if not loaded:
            load_documents()

    if not DOCUMENTS:
        return []

    semantic_results = _semantic_search(
        query,
        SEMANTIC_CANDIDATES
    )

    lexical_results = _lexical_search(
        query,
        LEXICAL_CANDIDATES
    )


    combined = {}

    for result in semantic_results:

        doc_id = result["id"]

        combined[doc_id] = {
            "source": result["source"],
            "content": result["content"],
            "id": doc_id,
            "semantic_score": result.get(
                "semantic_score",
                0.0
            ),
            "lexical_score": 0.0,
        }

    for result in lexical_results:

        doc_id = result["id"]

        if doc_id not in combined:

            combined[doc_id] = {
                "source": result["source"],
                "content": result["content"],
                "id": doc_id,
                "semantic_score": 0.0,
                "lexical_score": result.get(
                    "lexical_score",
                    0.0
                ),
            }

        else:

            combined[doc_id]["lexical_score"] = (
                result.get(
                    "lexical_score",
                    0.0
                )
            )

    results = []

    for item in combined.values():

        semantic_score = item[
            "semantic_score"
        ]

        lexical_score = item[
            "lexical_score"
        ]

        final_score = (
            semantic_score
            * SEMANTIC_WEIGHT
            +
            lexical_score
            * LEXICAL_WEIGHT
        )

        item["score"] = float(
            final_score
        )

        results.append(item)

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    final_results = []

    for result in results[:top_k]:

        final_results.append({
            "source": result["source"],
            "content": result["content"],
            "score": float(
                result["score"]
            ),
        })

    return final_results

load_documents()
