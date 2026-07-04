from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector

from config import DB_CONN, DB_POOL_MIN, DB_POOL_MAX

pool = ConnectionPool(
    conninfo=DB_CONN,
    min_size=DB_POOL_MIN,
    max_size=DB_POOL_MAX,
    configure=register_vector,
    open=True,
)

def mark_failed(key):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE documents SET status='FAILED', updated_at=now() WHERE  s3_key=%s",
                (key,),
            )