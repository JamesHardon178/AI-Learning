from transformers import AutoTokenizer


tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct"
)


def count_tokens(text: str) -> int:
    tokens = tokenizer.encode(text)
    return len(tokens)