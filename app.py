from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
# from modules.memory import get_messages

import os
import time

from modules.chat import (
    generate_text,
    chat_with_voice
)
from fastapi import Query
from modules.observability import log_event


app = FastAPI()


# ───── REQUEST ─────

class ChatRequest(BaseModel):

    message: str

    conversation_id: str


# ───── CHAT API ─────

@app.post("/chat")
def chat(req: ChatRequest):

    started = time.perf_counter()

    # Generar resposta
    text = generate_text(

        user_input=req.message,

        conversation_id=req.conversation_id

    )


    # Generar veu
    audio_path = chat_with_voice(
        text
    )


    total_ms = round((time.perf_counter() - started) * 1000, 2)
    log_event("request", route="/chat", latency_ms=total_ms)

    return {

        "text": text,

        "audio": f"/audio/{os.path.basename(audio_path)}",
        "observability": {"total_latency_ms": total_ms},

    }


# ───── AUDIO ─────

@app.get("/audio/{file_name}")
def get_audio(file_name: str):

    return FileResponse(file_name)



@app.post('/upload')
async def upload_knowledge(file: UploadFile = File(...)):

    # ensure knowledge folder exists
    os.makedirs("knowledge", exist_ok=True)

    filename = os.path.basename(file.filename)

    path = os.path.join("knowledge", filename)

    content = await file.read()

    with open(path, "wb") as f:

        f.write(content)

    # reindex documents
    try:

        from modules.rag import reindex

        reindex("knowledge")

    except Exception as error:
        log_event("reindex_error", error=str(error), source=filename)

        return {"filename": filename, "status": "saved", "indexed": False}

    return {"filename": filename, "status": "ok", "indexed": True}



# ───── MEMORY ─────

# @app.get("/memory/{conversation_id}")
# def get_memory(conversation_id: str):

#     return {
#         "conversation_id": conversation_id,
#         "messages": get_messages(conversation_id)
#     }


# ───── RETRIEVE ─────

@app.get('/debug/retrieve')
def debug_retrieve(q: str = Query(..., description="Query to retrieve from knowledge")):
    try:
        from modules.rag import retrieve

        snippets = retrieve(q, top_k=5)

        return {
            "query": q,
            "results": snippets,
            "result_count": len(snippets),
            "retrieval_ms": snippets[0].get("retrieval_ms", 0) if snippets else 0,
        }

    except Exception as e:
        return {"error": str(e)}

# ───── FRONTEND ─────

# The React app is built into frontend/dist. API routes above remain available
# at the same URLs for local clients and integrations.
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")