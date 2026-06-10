"""Conversational data assistant powered by Groq's Llama models."""

from groq import Groq

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are the PHCORE AI Analyst, embedded in a banking People Analytics \
dashboard (Predictive Human Capital & Operational Risk Engine). Answer questions using \
ONLY the dataset summary below - it covers HR, L&D/training, compliance certifications, \
and operational performance for a synthetic regional bank.

Be concise, cite specific numbers from the summary, and call out risk areas (high \
attrition, error rates above 2%, expiring certifications, low cross-sell) when relevant. \
If a question can't be answered from this summary, say so plainly rather than guessing.

DATA SUMMARY:
{data_context}
"""


def get_ai_response(api_key: str, data_context: str, chat_history: list[dict]) -> str:
    """Send the conversation plus a grounding data summary to Groq and return the reply."""
    client = Groq(api_key=api_key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(data_context=data_context)}]
    messages.extend(chat_history)

    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=600,
    )
    return completion.choices[0].message.content
