import io
import boto3
import json
import psycopg
import pypdf
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

DB_CONN = "host=localhost port=5433 dbname=docintel user=docuser password=docpass"
ENDPOINT = "http://localhost:4566"

sqs = boto3.client(
    "sqs",
    endpoint_url=ENDPOINT,
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

s3 = boto3.client("s3", endpoint_url=ENDPOINT, region_name="us-east-1", 
    aws_access_key_id="test", aws_secret_access_key="test")

model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model Loaded")

queue_url = sqs.get_queue_url(QueueName="docmind-jobs")["QueueUrl"]
print(f"Worker listening on {queue_url}")

def extract_text(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()
    reader = pypdf.PdfReader(io.BytesIO(data))
    text = "".join((page.extract_text() or "") for page in reader.pages)
    return text, len(reader.pages)

def chunk_text(text, size=1000, overlap=150):
    chunks=[]
    start = 0
    while start < len(text):
        chunk = text[start:start + size].strip()
        if chunk:
            chunks.append(chunk)
        start += size - overlap
    return chunks

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

    try: 
        text, pages = extract_text(bucket, key)
        chunks = chunk_text(text)
        embeddings = model.encode(chunks) if chunks else []

        with psycopg.connect(DB_CONN) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chunks WHERE document_id = %s", (doc_id,))
                for i, (content, emb) in enumerate(zip(chunks, embeddings)):
                    cur.execute(
                        "INSERT INTO chunks (document_id, chunk_index, content, embedding)"
                        "VALUES (%s, %s, %s, %s)",
                        (doc_id, i, content, emb),
                    )
                cur.execute(
                    "UPDATE documents SET status='READY', page_count=%s, updated_at=now() WHERE id=%s",
                    (pages,doc_id),
                )
        print(f"READY - > {key} ({pages} pages, {len(chunks)} chunks)")
    except Exception as e:
        with psycopg.connect(DB_CONN) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE documents SET status='FAILED', updated_at=now() WHERE id=%s", (doc_id,))
        print(f"FAILED -> {key}: {e}")


while True:
    response = sqs.receive_message(
        QueueUrl = queue_url,
        MaxNumberOfMessages=5,
        WaitTimeSeconds=10,
    )

    for message in response.get("Messages", []):
        body = json.loads(message["Body"])

        if body.get("Event") == "s3:TestEvent":
            print("Received S3 test event, skipping")
        else:
            for record in body.get("Records", []):
                process_record(record)
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
