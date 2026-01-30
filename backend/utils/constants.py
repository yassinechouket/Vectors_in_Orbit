
from pathlib import Path



IRREGULAR_FILE_EXTENSIONS = [".txt", ".md", ".html"]


CHUNK_OVERLAP = 50
CHUNK_SIZE = 500


N_RETRIES = 3  # Number of retry attempts for LLM calls that fail validation


# CV rewriting iteration configuration
MAX_ITER = 1
SIMILARITY_THRESHOLD = 0.97

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_PATHS = {
    "logs": PROJECT_ROOT / "logs",
    "data": PROJECT_ROOT / "data",
    "temp": PROJECT_ROOT / "temp",
}
