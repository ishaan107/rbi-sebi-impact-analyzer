"""
Unified LLM client so agent code doesn't care which provider is active.
Supports plain text generation and JSON-mode structured generation.
"""
import json
from src.config import LLM_PROVIDER, GEMINI_API_KEY, GROQ_API_KEY, GEMINI_MODEL, GROQ_MODEL


def _call_gemini(prompt: str, system: str | None = None) -> str:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=system)
    response = model.generate_content(prompt)
    return response.text


def _call_groq(prompt: str, system: str | None = None) -> str:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
    )
    return response.choices[0].message.content


def generate(prompt: str, system: str | None = None) -> str:
    """Plain text generation."""
    if LLM_PROVIDER == "gemini":
        return _call_gemini(prompt, system)
    elif LLM_PROVIDER == "groq":
        return _call_groq(prompt, system)
    raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")


def generate_json(prompt: str, system: str | None = None) -> dict:
    """
    Structured generation. Instructs the model to return ONLY JSON,
    then parses it. Strips markdown code fences defensively.
    """
    json_instruction = (
        "\n\nIMPORTANT: Respond with ONLY valid JSON. No preamble, "
        "no markdown code fences, no explanation text."
    )
    raw = generate(prompt + json_instruction, system)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON. Raw output:\n{raw}") from e
