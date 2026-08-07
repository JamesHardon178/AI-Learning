import json
import requests


def chat_with_llm_stream(prompt: str):

    url = "http://127.0.0.1:11434/api/generate"

    payload = {
        "model": "qwen2.5:0.5b",
        "prompt": prompt,
        "stream": True
    }

    response = requests.post(
        url,
        json=payload,
        stream=True,
        timeout=60
    )

    for chunk in response.iter_lines():

        if chunk:

            data = json.loads(
                chunk.decode("utf-8")
            )

            content = data.get(
                "response",
                ""
            )

            if content:
                yield content