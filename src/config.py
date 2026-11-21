from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
KB_DIR = DATA_DIR / "kb"
DB_DIR = ROOT / "db"
INDEX_DIR = ROOT / "index"
MEMORY_DIR = ROOT / "memory"
LOGS_DIR = ROOT / "logs"
RESULTS_DIR = ROOT / "results"
SKILLS_DIR = ROOT / "skills"

VARIANT = "V31"
DOMAIN = "Clinic appointment desk"
TWIST = "B. Time-bound facts"
WINDOW_K = 5
CONTEXT_WINDOW = 4096
SCALE_DAILY_USERS = 5000

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
EMBEDDING_POOLING = "mean"
# Set RECALLBOT_EMBED_BACKEND=hash to force offline hashing embeddings (corporate SSL).

CHAT_MODEL = "template-nlg"
OLLAMA_MODEL = "qwen2.5:1.5b-instruct"
OLLAMA_HOST = "http://127.0.0.1:11434"

CHUNK_SIZES = (128, 512)
CHUNK_OVERLAP_RATIO = 0.15
BM25_K1 = 1.5
BM25_B = 0.75
RRF_K = 60

FALLBACK_SENTENCE = (
    "I do not have that information in the clinic knowledge base or your saved profile."
)

AS_OF_DATE_DEFAULT = "2026-11-21"
