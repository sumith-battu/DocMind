import os

# --- AWS ---
AWS_ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")            # unset in real AWS
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
QUEUE_NAME = os.getenv("SQS_QUEUE_NAME", "docmind-jobs")

# --- Database ---
DB_CONN = (
    f"host={os.getenv('DB_HOST', 'localhost')} "
    f"port={os.getenv('DB_PORT', '5433')} "
    f"dbname={os.getenv('DB_NAME', 'docintel')} "
    f"user={os.getenv('DB_USER', 'docuser')} "
    f"password={os.getenv('DB_PASSWORD', 'docpass')}"
)

DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "1"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "5"))


# --- Embedding / chunking ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "128"))


# --- Worker ---
MAX_RECEIVE_COUNT = int(os.getenv("MAX_RECEIVE_COUNT", "3"))