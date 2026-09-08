from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
# from modules.memory import get_messages

import os

from modules.chat import (
    generate_text,
    chat_with_voice
)
from fastapi import Query


app = FastAPI()


# ───── REQUEST ─────

class ChatRequest(BaseModel):

    message: str

    conversation_id: str


# ───── CHAT API ─────

@app.post("/chat")
def chat(req: ChatRequest):

    # Generar resposta
    text = generate_text(

        user_input=req.message,

        conversation_id=req.conversation_id

    )


    # Generar veu
    audio_path = chat_with_voice(
        text
    )


    return {

        "text": text,

        "audio":
            f"/audio/{os.path.basename(audio_path)}"

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

    except Exception:

        pass

    return {"filename": filename, "status": "ok"}



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

        return {"query": q, "results": snippets}

    except Exception as e:
        return {"error": str(e)}

# ───── FRONTEND ─────

# The React app is built into frontend/dist. API routes above remain available
# at the same URLs for local clients and integrations.
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")