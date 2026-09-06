from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import time




MODEL_NAME = "Qwen/Qwen3.5-0.8B"

print("CUDA disponible:", torch.cuda.is_available())

if torch.cuda.is_available():

    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )

    print(
        "VRAM total:",
        round(
            torch.cuda.get_device_properties(0).total_memory
            / 1024**3,
            2
        ),
        "GB"
    )


#Load model

print("\nCarregant Qwen...")

start = time.time()


tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)


model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,

    device_map="auto",

    torch_dtype=(
        torch.float16
        if torch.cuda.is_available()
        else torch.float32
    )
)


model.eval()


load_time = time.time() - start


print(
    f"Model carregat en {load_time:.2f} segons"
)


print("\n──── DEVICE MAP ────")


if hasattr(model, "hf_device_map"):

    print(model.hf_device_map)

else:

    print("No hi ha hf_device_map")


print("────────────────────")

if torch.cuda.is_available():

    print("\n──── GPU MEMORY ────")

    print(
        "VRAM reservada:",
        round(
            torch.cuda.memory_reserved(0)
            / 1024**3,
            2
        ),
        "GB"
    )

    print(
        "VRAM assignada:",
        round(
            torch.cuda.memory_allocated(0)
            / 1024**3,
            2
        ),
        "GB"
    )

    print("────────────────────")


#Generate text with the model

def generate_qwen(messages):

    """
    Rep una llista de messages amb el format:

    [
        {
            "role": "system",
            "content": "..."
        },
        {
            "role": "user",
            "content": "..."
        }
    ]

    i retorna només la resposta generada per Qwen.
    """


    # Chat template

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # Tokenizer

    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    ).to(model.device)

    # Generation

    with torch.no_grad():

        # Use low-temperature deterministic decoding to reduce contradictions with retrieved knowledge
        output = model.generate(

            **inputs,

            max_new_tokens=200,

            do_sample=False,

            temperature=0.2,

            top_p=1.0,

            repetition_penalty=1.05
        )


    new_tokens = output[
        0
    ][
        inputs["input_ids"].shape[1]:
    ]

    text = tokenizer.decode(
        new_tokens,
        skip_special_tokens=True
    ).strip()


    return text


# Warm-Up the model to reduce the first inference latency

print("\nQwen carregat. Fent warm-up...")


_dummy_messages = [

    {
        "role": "system",
        "content": "Respon breument."
    },

    {
        "role": "user",
        "content": "Hola"
    }

]


start = time.time()


_dummy_response = generate_qwen(
    _dummy_messages
)


warmup_time = time.time() - start


print(
    f"Warm-up acabat en {warmup_time:.2f} segons"
)


print(
    "Resposta del warm-up:",
    _dummy_response
)

# GPU check after warm-up

if torch.cuda.is_available():

    print("\n──── GPU MEMORY AFTER WARM-UP ────")

    print(
        "VRAM reservada:",
        round(
            torch.cuda.memory_reserved(0)
            / 1024**3,
            2
        ),
        "GB"
    )

    print(
        "VRAM assignada:",
        round(
            torch.cuda.memory_allocated(0)
            / 1024**3,
            2
        ),
        "GB"
    )

    print("────────────────────────────────")


print("\nQwen preparat!")