"""Build KB chunk indexes for chunk sizes 128 and 512."""

from src.logging_util import set_run_id
from src.retrieval import build_all_indexes


def main():
    set_run_id("r_index")
    indexes = build_all_indexes(as_config="hybrid")
    for size, idx in indexes.items():
        print(f"chunk_size={size} chunks={len(idx.chunks)}")


if __name__ == "__main__":
    main()
