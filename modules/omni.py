import uuid

from omnivoice import OmniVoice

import soundfile as sf
import torch


# ─────────────────────────────────────
# CONFIGURACIÓ
# ─────────────────────────────────────

MODEL_NAME = "k2-fsa/OmniVoice"

REF_AUDIO = "Nero.wav"


# ─────────────────────────────────────
# CARREGAR OMNIVOICE
# ─────────────────────────────────────

print("Carregant OmniVoice...")


model = OmniVoice.from_pretrained(
    MODEL_NAME,
    device_map="cuda:0",
    dtype=torch.float16
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


    file_path = (
        f"audio_{uuid.uuid4().hex}.wav"
    )


    sf.write(
        file_path,
        audio[0],
        24000
    )


    return file_path