from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from modules.omni import omnivoice_generate 
model_name = "Qwen/Qwen3.5-0.8B"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)

def generate_text(user_input):
    messages = [
        {"role": "system", "content": "Ets un assistent útil que parla en català."},
        {"role": "user", "content": user_input}
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    output = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.7
    )

    return tokenizer.decode(output[0], skip_special_tokens=True)

def chat_with_voice(user_input):
    text = generate_text(user_input)

    audio_path = omnivoice_generate(text)  

    return audio_path