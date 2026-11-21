"""One-command pipeline for Prayogshala / local full evidence runs."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("\n==>", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=ROOT)


def clear_runtime(keep_logs: bool = True) -> None:
    for name in ("memory", "db"):
        path = ROOT / name
        if path.exists():
            for child in path.iterdir():
                if child.name == ".gitkeep":
                    continue
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    child.unlink(missing_ok=True)
    if not keep_logs:
        log = ROOT / "logs" / "calls.jsonl"
        if log.exists():
            log.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--embed-backend",
        default="",
        help="hash | sentence-transformers (empty = auto; Prefer empty on Prayogshala)",
    )
    parser.add_argument("--skip-ablation", action="store_true")
    parser.add_argument("--skip-hnsw", action="store_true")
    parser.add_argument("--fresh-logs", action="store_true")
    args = parser.parse_args()

    env_prefix = []
    py = sys.executable

    if args.embed_backend:
        # Applied inside child processes via os.environ in wrapper commands.
        import os

        os.environ["RECALLBOT_EMBED_BACKEND"] = args.embed_backend

    clear_runtime(keep_logs=not args.fresh_logs)

    run([py, "scripts/generate_task1_data.py"])
    run([py, "-m", "pytest", "tests/", "-q"])
    run([py, "-m", "src.build_index"])
    run([py, "-m", "src.eval_nlu"])
    run([py, "-m", "src.eval_retrieval"])

    # Primary hybrid_mem path (Session B must be a separate process).
    clear_runtime(keep_logs=True)
    run([py, "-m", "src.run_session", "--session", "A", "--config", "hybrid_mem", "--run-id", "r_hm_A"])
    run([py, "-m", "src.run_session", "--session", "B", "--config", "hybrid_mem", "--run-id", "r_hm_B"])
    run([py, "-m", "src.eval_probes", "--config", "hybrid_mem", "--run-id", "r_hm_probes"])
    run([py, "-m", "src.eval_semantic"])
    run([py, "-m", "src.eval_episodic_weights"])

    # STM strategies
    for cfg in ("full", "trim", "summary"):
        clear_runtime(keep_logs=True)
        run([py, "-m", "src.run_session", "--session", "A", "--config", cfg, "--run-id", f"r_{cfg}_A"])
    run([py, "-m", "src.plot_tokens"])

    if not args.skip_ablation:
        for cfg in ("no_rag", "hybrid", "hybrid_sem", "hybrid_mem"):
            clear_runtime(keep_logs=True)
            run([py, "-m", "src.run_session", "--session", "A", "--config", cfg, "--run-id", f"r_{cfg}_A2"])
            run([py, "-m", "src.run_session", "--session", "B", "--config", cfg, "--run-id", f"r_{cfg}_B2"])
            run([py, "-m", "src.eval_probes", "--config", cfg, "--run-id", f"r_{cfg}_probes"])
        run([py, "-m", "src.eval_ablation"])

    if not args.skip_hnsw:
        run([py, "-m", "src.cost_scale"])

    print("\nAll pipeline steps finished.")
    print("Artifacts: logs/calls.jsonl, results/, memory/, index/")


if __name__ == "__main__":
    main()
