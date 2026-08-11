import uuid
from omnivoice import OmniVoice
import soundfile as sf
import torch

def omnivoice_generate(t):
    model = OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice",
        device_map="cuda:0",
        dtype=torch.float16
    )

    audio = model.generate(
        text=t,
        ref_audio="Nero.wav",
    ) 
    file_path = f"audio_{uuid.uuid4().hex}.wav"
    sf.write(file_path, audio[0], 24000)
    return file_path
