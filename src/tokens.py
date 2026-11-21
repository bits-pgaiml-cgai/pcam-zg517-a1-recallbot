from functools import lru_cache


@lru_cache(maxsize=1)
def get_tokenizer():
    try:
        import tiktoken

        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def count_tokens(text: str) -> int:
    if not text:
        return 0
    enc = get_tokenizer()
    if enc is not None:
        return len(enc.encode(text))
    return max(1, len(text.split()))


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    enc = get_tokenizer()
    if enc is None:
        words = text.split()
        return " ".join(words[:max_tokens])
    ids = enc.encode(text)
    if len(ids) <= max_tokens:
        return text
    return enc.decode(ids[:max_tokens])
