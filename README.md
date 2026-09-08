### OmniCar — local RAG-enabled chatbot

Small local chatbot that combines a local LLM (Qwen), a voice generator (OmniVoice), and a simple RAG (retrieval-augmented generation) pipeline. Upload text or markdown files to `knowledge/` and the bot will use them to answer and cite sources.

# Quick start
   1. Create and activate a Python virtualenv.
   2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   # optional (for better retrieval quality):
   pip install sentence-transformers numpy
   ```
   3. Start the FastAPI backend:
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```
   4. In a second terminal, install and run the React frontend during development:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   5. Open the UI: http://127.0.0.1:5173/ or localhost:8000

## Production frontend

Build the React app and FastAPI will serve it from `/` while keeping all API endpoints available:

```bash
cd frontend
npm install
npm run build
cd ..
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000/ after the build.

# Main endpoints
- `GET /` — React web UI (served from `frontend/dist` after a production build)
- `POST /chat` — chat API; JSON body: `{ "message": "...", "conversation_id": "..." }`
- `POST /upload` — upload a `.txt` or `.md` file (multipart form `file`) — saves to `knowledge/` and reindexes
- `GET /debug/retrieve?q=...` — returns retrieved snippets for a query (useful to debug RAG)
- `GET /knowledge` — lists indexed documents (shows whether embeddings are present)
- `GET /audio/{file_name}` — serves generated audio files
- `GET /memory/{conversation_id}` — returns conversation history saved in `chat.db`

# How RAG works
- Uploaded files are split into chunks and indexed in memory at startup or after uploads.
- If `sentence-transformers` is installed, chunks are embedded with `all-MiniLM-L6-v2` and retrieval uses cosine similarity.
- If embeddings are not available the code falls back to a token-overlap heuristic (less accurate).

# Development notes
- Knowledge files are stored in the `knowledge/` folder at project root. Filenames are used as citation sources.
- Conversation history is saved in `chat.db` using SQLite.
- To change the local LLM or voice model, edit `modules/qwen.py` and `modules/omni.py` respectively.
