import fitz
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL, CHUNK_SIZE, OVERLAP, BATCH_SIZE
from db import pool

print("Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)
print("Model loaded.")


def embed_and_insert(cur, doc_id, batch, start_index):
    embeddings = model.encode(batch)
    for offset, (content, emb) in enumerate(zip(batch, embeddings)):
        cur.execute(
            "INSERT INTO chunks (document_id, chunk_index, content, embedding) "
            "VALUES (%s, %s, %s, %s)",
            (doc_id, start_index + offset, content, emb),
        )
    return start_index + len(batch)


def extract_and_index(doc_id, path):
    doc = fitz.open(path)
    page_count = doc.page_count
    print(f"Started processing: {page_count} pages")

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chunks WHERE document_id = %s", (doc_id,))

                buffer = ""
                batch = []
                chunk_index = 0

                for i, page in enumerate(doc):
                    buffer += clean_text(page.get_text() or "") + " "
                    while len(buffer) >= CHUNK_SIZE:
                        chunk = buffer[:CHUNK_SIZE].strip()
                        if chunk:
                            batch.append(chunk)
                        buffer = buffer[CHUNK_SIZE - OVERLAP:]
                        if len(batch) >= BATCH_SIZE:
                            chunk_index = embed_and_insert(cur, doc_id, batch, chunk_index)
                            batch = []

                    if (i + 1) % 100 == 0:
                        print(f"  page {i + 1}/{page_count}, {chunk_index} chunks indexed")

                tail = buffer.strip()
                if tail:
                    batch.append(tail)
                if batch:
                    chunk_index = embed_and_insert(cur, doc_id, batch, chunk_index)

                cur.execute(
                    "UPDATE documents SET status='READY', page_count=%s, updated_at=now() WHERE id=%s",
                    (page_count, doc_id),
                )
    finally:
        doc.close()

    print(f"Completed processing: {chunk_index} chunks")
    return page_count, chunk_index