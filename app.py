from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from modules.memory import get_messages

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

@app.get("/memory/{conversation_id}")
def get_memory(conversation_id: str):

    return {
        "conversation_id": conversation_id,
        "messages": get_messages(conversation_id)
    }


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

@app.get(
    "/",
    response_class=HTMLResponse
)
def home():

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <title>Chatbot local</title>

        <style>

            body {

                font-family: Arial;

                max-width: 600px;

                margin: auto;

                padding-top: 50px;

            }

            input {

                width: 80%;

                padding: 10px;

            }

            button {

                padding: 10px;

            }

            #response {

                margin-top: 20px;

                white-space: pre-wrap;

            }

        </style>

    </head>


    <body>

        <h2>🤖 Chatbot local</h2>


        <input
            id="msg"
            placeholder="Escriu aquí..."
        />


        <button onclick="send()">
            Enviar
        </button>


        <div id="response"></div>


        <audio
            id="audio"
            controls
        ></audio>


        <script>


        // ─────────────────────────
        // CONVERSATION ID
        // ─────────────────────────

        let conversationId =
            localStorage.getItem(
                "conversation_id"
            );


        if (!conversationId) {

            conversationId =
                crypto.randomUUID();


            localStorage.setItem(
                "conversation_id",
                conversationId
            );

        }


        // ─────────────────────────
        // SEND
        // ─────────────────────────

        async function send() {

            const input =
                document.getElementById(
                    "msg"
                );


            const msg =
                input.value.trim();


            if (!msg) {

                return;

            }


            input.value = "";


            const res = await fetch(
                "/chat",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        message: msg,

                        conversation_id:
                            conversationId

                    })

                }
            );


            const data =
                await res.json();


            // Mostrar text
            document.getElementById(
                "response"
            ).innerText = data.text;


            // Reproduir audio
            const audio =
                document.getElementById(
                    "audio"
                );


            audio.src = data.audio;

            audio.play();

        }


        </script>

    </body>

    </html>
    """