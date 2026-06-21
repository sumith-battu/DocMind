import os
import json
import tempfile
import boto3
import psycopg
import pypdf
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

# --- Config: env vars with local-dev defaults ---
AWS_ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")            # unset in real AWS
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
QUEUE_NAME = os.getenv("SQS_QUEUE_NAME", "docmind-jobs")

DB_CONN = (
    f"host={os.getenv('DB_HOST', 'localhost')} "
    f"port={os.getenv('DB_PORT', '5433')} "
    f"dbname={os.getenv('DB_NAME', 'docintel')} "
    f"user={os.getenv('DB_USER', 'docuser')} "
    f"password={os.getenv('DB_PASSWORD', 'docpass')}"
)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))

sqs = boto3.client("sqs", endpoint_url=AWS_ENDPOINT, region_name=AWS_REGION,
                   aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
s3 = boto3.client("s3", endpoint_url=AWS_ENDPOINT, region_name=AWS_REGION,
                  aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

print("Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)
print("Model loaded.")

queue_url = sqs.get_queue_url(QueueName=QUEUE_NAME)["QueueUrl"]
print(f"Worker listening on {queue_url}")

def download_to_temp(bucket, key):
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    s3.download_file(bucket,key,path)
    return path

# def extract_text(bucket, key):
#     obj = s3.get_object(Bucket=bucket, Key=key)
#     data = obj["Body"].read()
#     reader = pypdf.PdfReader(io.BytesIO(data))
#     text = "".join((page.extract_text() or "") for page in reader.pages)
#     return text, len(reader.pages)

# def chunk_text(text, size=1000, overlap=150):
#     chunks=[]
#     start = 0
#     while start < len(text):
#         chunk = text[start:start + size].strip()
#         if chunk:
#             chunks.append(chunk)
#         start += size - overlap
#     return chunks

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
    reader = pypdf.PdfReader(path)
    page_count = len(reader.pages)
    print(f"Started processing: {page_count} pages")

    with psycopg.connect(DB_CONN) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chunks WHERE document_id = %s", (doc_id,))

            buffer = ""
            batch = []
            chunk_index = 0

            for i, page in enumerate(reader.pages):
                buffer += (page.extract_text() or "")
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

    print(f"Completed processing: {chunk_index} chunks")
    return page_count, chunk_index

def mark_failed(key):
    with psycopg.connect(DB_CONN) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE documents SET status='FAILED', updated_at=now() WHERE s3_key=%s",(key,))

def process_record(record):
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    with psycopg.connect(DB_CONN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM documents WHERE s3_key = %s", (key,))
            row = cur.fetchone()
            if not row:
                print(f"No document for key {key}")
                return
            doc_id = row[0]
            cur.execute("UPDATE documents SET status='PROCESSING', updated_at=now() WHERE id=%s", (doc_id,))
    tmp_path = None
    try: 
        tmp_path = download_to_temp(bucket, key)
        page_count, chunk_count = extract_and_index(doc_id, tmp_path)
        print(f"READY -> {key} ({page_count} pages, {chunk_count} chunks)")
    # except Exception as e:
    #     with psycopg.connect(DB_CONN) as conn:
    #         with conn.cursor() as cur:
    #             cur.execute("UPDATE documents SET status='FAILED', updated_at=now() WHERE id=%s", (doc_id,))
    #     print(f"FAILED -> {key}: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


MAX_RECEIVE_COUNT = 3

while True:
    response = sqs.receive_message(
        QueueUrl = queue_url,
        MaxNumberOfMessages=5,
        WaitTimeSeconds=10,
        AttributeNames=["ApproximateReceiveCount"],
    )

    for message in response.get("Messages", []):
        receive_count = int(message.get("Attributes", {}).get("ApproximateReceiveCount", "1"))
        body = json.loads(message["Body"])

        if body.get("Event") == "s3:TestEvent":
            print("Received S3 test event, skipping")
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
            continue
        try:
            for record in body.get("Records", []):
                process_record(record)
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
        except Exception as e:
            print(f"Processing failed (attempt {receive_count}/{MAX_RECEIVE_COUNT}): {e}")
            if receive_count >= MAX_RECEIVE_COUNT:
                for record in body.get("Records", []):
                    mark_failed(record["s3"]["object"]["key"])
