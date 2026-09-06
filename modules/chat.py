from modules.qwen import generate_qwen

from modules.memory import (
    init_db,
    get_messages,
    save_message
)

from modules.omni import omnivoice_generate
from modules.rag import retrieve


# Create the database 
init_db()


SYSTEM_PROMPT = """
You are a helpful conversational assistant.

Always answer in English.
Use the conversation history to maintain context.
If the user tells you their name, remember it.
If they ask for their name later, answer directly.
Do not invent information.
Keep your answers concise and natural.
When relevant, prefer information from provided knowledge snippets and cite the source name (e.g., "Source: filename.md").
If the user's question can be answered using the knowledge snippets, answer using those facts and do not contradict them.
If the knowledge snippets contain an explicit answer to the user's question, respond using only that information and cite the source. If you are unsure, say "I don't know" rather than inventing answers.
"""


def generate_text(
    user_input,
    conversation_id
):

    # Get conversation history from the database
    history = get_messages(
        conversation_id
    )


    # Build the conversation
    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }

    ]


    # Retrieve relevant knowledge snippets (RAG) and merge into the
    # initial system message. The chat template requires the system
    # message to be the first (and only) system role entry.
    try:
        snippets = retrieve(user_input, top_k=3)
    except Exception:
        snippets = []

    if snippets:

        knowledge_text = "\n\n---\n\n".join(
            [f"Source: {s['source']}\n{s['content']}" for s in snippets]
        )

        # append knowledge to the existing system prompt
        messages[0]["content"] = (
            messages[0]["content"]
            + "\n\nRelevant knowledge snippets:\n\n"
            + knowledge_text
        )


    messages.extend(history)
    print(f"Message: {messages[0]['content']}")

    messages.append({

        "role": "user",

        "content": user_input

    })


    # Ask Qwen
    text = generate_qwen(
        messages
    )


    # Save user message
    save_message(
        conversation_id,
        "user",
        user_input
    )


    # Save answer
    save_message(
        conversation_id,
        "assistant",
        text
    )


    return text


def chat_with_voice(text):

    return omnivoice_generate(text)