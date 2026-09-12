# Vellum

Vellum is a local english voice assistant that answers questions from a small, user-owned knowledge base. It demonstrates a measurable retrieval-augmented generation (RAG) system rather than a general-purpose agent: documents are indexed locally, answers use retrieved evidence, and unsupported questions receive a clear no-answer response.

## Features

- TXT and Markdown ingestion with paragraph-aware overlapping chunks
- Hybrid semantic and lexical retrieval
- Embedding fallback when `sentence-transformers` or FAISS is unavailable
- Source and chunk citations, snippets, and retrieval scores
- Knowledge inspector for query, source, score components, metadata, and latency
- Deterministic no-answer handling below the evidence threshold
- Local Qwen generation and optional OmniVoice text-to-speech
- Accessible play, pause, stop, speed, status, keyboard, and reduced-motion controls
- Lightweight JSON pipeline logs for embedding, vector search, retrieval, generation, TTS, and request latency


## RAG pipeline

1. Files in `knowledge/` are read as UTF-8 TXT or Markdown and split into chunks up to 800 characters with 150 characters of overlap.
2. `all-MiniLM-L6-v2` embeddings are normalized and indexed with FAISS when available. The same chunks remain searchable with token-overlap scoring as a lightweight fallback.
3. Semantic and lexical candidates are merged using a 75/25 weighted score. Each result includes the source path, chunk ID, component scores, character count, and retrieval latency.
4. Results below the minimum evidence score are discarded. The assistant returns a deterministic no-answer message instead of asking the LLM to guess.
5. Relevant chunks are placed in the system prompt. The response is required to cite sources, and the backend adds a source footer if the model omits one.

## Observability

The `vellum` logger emits one-line JSON events suitable for local development. Events include `embedding`, `vector_search`, `retrieval`, `llm_generation`, `tts`, `request`, and error/no-answer events. No external telemetry service is required.

## Run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

For frontend development, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

For a single production server:

```bash
cd frontend && npm install && npm run build
cd ..
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` or `http://localhost:8000` after the production build, or the Vite URL during development.

## Run with Docker

Docker is optional and does not replace the local workflow above. The image builds the React frontend and runs the FastAPI app with NVIDIA CUDA 12.8 and cuDNN:

```bash
docker compose up --build
```

Open `http://localhost:8000`. Uploaded files are kept in the local `knowledge/` and `audio/` directories; downloaded model files and the retrieval index are stored in Docker volumes. The image requires an NVIDIA GPU because it installs CUDA-enabled PyTorch wheels. Stop it with:

```bash
docker compose down
```

The Docker image uses the same application code and does not affect `venv`, `npm run dev`, or the existing local commands. Docker Desktop must have GPU support enabled, and the host needs a compatible NVIDIA driver and NVIDIA Container Toolkit. Verify GPU access with `docker run --rm --gpus all nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04 nvidia-smi` before starting the app.


## API and limitations

- `POST /chat` accepts `{ "message": "...", "conversation_id": "..." }` and returns text, audio, and total latency.
- `POST /upload` accepts `.txt` or `.md` files and reindexes the knowledge directory.
- `GET /debug/retrieve?q=...` exposes retrieval records used by the inspector.
- `GET /audio/{file_name}` serves generated audio files.

The embedding and generation models can be slow on CPU, the lexical fallback is less capable than embeddings, supportedness is evaluated with retrieval evidence and simple checks rather than a separate judge model, and uploaded files are trusted local input. Conversation history is not used to influence RAG answers.

The model used is a very small Qwen model, so English currently provides the best results. The model can be easily replaced with a larger one to achieve better results in other languages.
