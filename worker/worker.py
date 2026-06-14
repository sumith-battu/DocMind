import io
import boto3
import json
import psycopg
import pypdf

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


queue_url = sqs.get_queue_url(QueueName="docmind-jobs")["QueueUrl"]
print(f"Worker listening on {queue_url}")

def update_status(s3_key, status, page_count=None):
    with psycopg.connect(DB_CONN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE documents SET status = %s, page_count = %s, updated_at = now() "
                "WHERE s3_key = %s",
                (status, page_count, s3_key),
            )
            return cur.rowcount

def extract_text(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()
    reader = pypdf.PdfReader(io.BytesIO(data))
    text = "".join((page.extract_text() or "") for page in reader.pages)
    return text, len(reader.pages)

def process_record(record):
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    update_status(key, "PROCESSING")

    try: 
        text, pages = extract_text(bucket, key)
        update_status(key, "READY", page_count=pages)
        print(f"READY - > {key} ({pages} pages, {len(text)} chars)")
    except Exception as e:
        update_status(key, "FAILED")
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
