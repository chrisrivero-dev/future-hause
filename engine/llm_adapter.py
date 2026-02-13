import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "llama3.1:latest"


def call_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Minimal Ollama adapter.
    Returns raw text response from model.
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()
    return data.get("response", "").strip()
