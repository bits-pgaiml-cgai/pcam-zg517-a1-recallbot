from typing import Dict, List

from src.tokens import count_tokens, get_tokenizer


def _encode(text: str) -> List[int]:
    enc = get_tokenizer()
    if enc is None:
        return text.split()
    return enc.encode(text)


def _decode(ids) -> str:
    enc = get_tokenizer()
    if enc is None:
        return " ".join(ids)
    return enc.decode(ids)


def chunk_text(
    text: str,
    chunk_size: int,
    overlap_ratio: float = 0.15,
    doc_id: str = "",
    section: str = "",
    version: str = "",
    valid_from: str = "",
    valid_to: str = "",
) -> List[Dict]:
    ids = _encode(text)
    if not ids:
        return []
    overlap = max(1, int(chunk_size * overlap_ratio))
    step = max(1, chunk_size - overlap)
    chunks = []
    start = 0
    idx = 0
    while start < len(ids):
        end = min(len(ids), start + chunk_size)
        piece = _decode(ids[start:end])
        chunks.append(
            {
                "chunk_id": f"{doc_id}::c{idx}",
                "doc_id": doc_id,
                "section": section,
                "version": version,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "text": piece,
                "token_count": count_tokens(piece),
                "chunk_size_setting": chunk_size,
            }
        )
        idx += 1
        if end >= len(ids):
            break
        start += step
    return chunks
