import os
import uuid

from omnivoice import OmniVoice

import soundfile as sf
import torch


# ─────────────────────────────────────
# CONFIGURACIÓ
# ─────────────────────────────────────

MODEL_NAME = "k2-fsa/OmniVoice"

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_AUDIO = os.path.join(PROJECT_DIR, "voices", "Girl.wav")
AUDIO_DIR = os.path.join(PROJECT_DIR, "audio")


# ─────────────────────────────────────
# CARREGAR OMNIVOICE
# ─────────────────────────────────────

print("Carregant OmniVoice...")


model = OmniVoice.from_pretrained(
    MODEL_NAME,
    device_map="cuda:0" if torch.cuda.is_available() else "cpu",
    dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)


print("OmniVoice carregat!")


# ─────────────────────────────────────
# GENERAR ÀUDIO
# ─────────────────────────────────────

def omnivoice_generate(text):

    audio = model.generate(
        text=text,
        ref_audio=REF_AUDIO,
    )


    os.makedirs(AUDIO_DIR, exist_ok=True)
    file_path = os.path.join(
        AUDIO_DIR,
        f"audio_{uuid.uuid4().hex}.wav"
    )


    sf.write(
        file_path,
        audio[0],
        24000
    )


    return file_path