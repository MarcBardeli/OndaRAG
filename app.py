from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import uuid
import os
from modules.chat import generate_text, chat_with_voice

app = FastAPI()

# ───── MODEL ─────
model_name = "Qwen/Qwen3.5-0.8B"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)

# ───── REQUEST ─────
class ChatRequest(BaseModel):
    message: str


# ───── API CHAT ─────
@app.post("/chat")
def chat(req: ChatRequest):
    text = generate_text(req.message)

    audio_path = chat_with_voice(text)

    return {
        "text": text,
        "audio": f"/audio/{os.path.basename(audio_path)}"
    }


# ───── SERVIR AUDIO ─────
@app.get("/audio/{file_name}")
def get_audio(file_name: str):
    return FileResponse(file_name)


# ───── FRONTEND ─────
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chatbot local</title>
        <style>
            body { font-family: Arial; max-width: 600px; margin: auto; padding-top: 50px; }
            input { width: 80%; padding: 10px; }
            button { padding: 10px; }
            #response { margin-top: 20px; white-space: pre-wrap; }
        </style>
    </head>
    <body>

        <h2>🤖 Chatbot local</h2>

        <input id="msg" placeholder="Escriu aquí..." />
        <button onclick="send()">Enviar</button>

        <div id="response"></div>
        <audio id="audio" controls></audio>

        <script>
        async function send() {
            const msg = document.getElementById("msg").value;

            const res = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({message: msg})
            });

            const data = await res.json();

            document.getElementById("response").innerText = data.text;

            const audio = document.getElementById("audio");
            audio.src = data.audio;
            audio.play();
        }
        </script>

    </body>
    </html>
    """