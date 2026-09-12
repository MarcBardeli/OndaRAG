from modules.rag import retrieve
from modules.observability import log_event, measure_stage


SYSTEM_PROMPT = """
You are a helpful knowledge-based assistant.

Always answer in English.
Do not invent information.
Keep your answers concise and natural.
Use the provided knowledge snippets as your primary source and cite the source name (e.g., "Source: filename.md").
If the user's question can be answered using the knowledge snippets, answer using those facts and do not contradict them.
If the knowledge snippets contain an explicit answer to the user's question, respond using only that information and cite the source. If you are unsure, say "I don't know" rather than inventing answers.
"""

NO_ANSWER = (
    "I couldn't find enough relevant information in the provided documents "
    "to answer that reliably."
)


def _has_relevant_context(snippets):
    return bool(snippets and snippets[0].get("score", 0.0) >= 0.18)


def _ensure_citations(text, snippets):
    if "source:" in text.lower() or "sources:" in text.lower():
        return text
    sources = ", ".join(dict.fromkeys(item["source"] for item in snippets))
    return f"{text.rstrip()}\n\nSources: {sources}"


def generate_text(
    user_input,
    conversation_id
):
    # Build a stateless request so old conversations cannot influence RAG answers.
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
        with measure_stage("retrieval", query=user_input):
            snippets = retrieve(user_input, top_k=3)
    except Exception as error:
        log_event("retrieval_error", error=str(error))
        snippets = []

    if not _has_relevant_context(snippets):
        log_event("rag_no_answer", query=user_input)
        return NO_ANSWER

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


    messages.append({

        "role": "user",

        "content": user_input

    })


    # Ask Qwen
    from modules.qwen import generate_qwen

    with measure_stage("llm_generation"):
        text = generate_qwen(messages)

    return _ensure_citations(text, snippets)


def chat_with_voice(text):
    from modules.omni import omnivoice_generate

    with measure_stage("tts"):
        return omnivoice_generate(text)