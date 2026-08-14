import json
import requests


def chat_with_llm_stream(prompt: str):

    url = "http://127.0.0.1:11434/api/generate"

    payload = {
    "model": "qwen2.5:0.5b",
    "prompt": prompt,
    "stream": True,
    "options": {
        "temperature": 0
    }
}

    with requests.post(
        url,
        json=payload,
        stream=True,
        timeout=(10, 300)
    ) as response:
        response.raise_for_status()

        # requests defaults to a 512-byte read buffer, which can hold back
        # short Ollama tokens until the model has nearly finished.
        for chunk in response.iter_lines(
            chunk_size=1,
            decode_unicode=True
        ):
            if not chunk:
                continue

            data = json.loads(chunk)
            content = data.get("response", "")

            if content:
                yield content
