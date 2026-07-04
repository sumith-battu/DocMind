import json
import os
import boto3

from config import (
    AWS_ENDPOINT, AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY,
    QUEUE_NAME, MAX_RECEIVE_COUNT,
)
from db import pool, mark_failed
from storage import download_to_temp
from pipeline import extract_and_index

sqs = boto3.client(
    "sqs",
    endpoint_url=AWS_ENDPOINT,
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

queue_url = sqs.get_queue_url(QueueName=QUEUE_NAME)["QueueUrl"]
print(f"Worker listening on {queue_url}")


def process_record(record):
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM documents WHERE s3_key = %s", (key,))
            row = cur.fetchone()
            if not row:
                print(f"No document for key {key}")
                return
            doc_id = row[0]
            cur.execute(
                "UPDATE documents SET status='PROCESSING', updated_at=now() WHERE id=%s",
                (doc_id,),
            )

    tmp_path = None
    try:
        tmp_path = download_to_temp(bucket, key)
        page_count, chunk_count = extract_and_index(doc_id, tmp_path)
        print(f"READY -> {key} ({page_count} pages, {chunk_count} chunks)")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def main():
    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
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
                    try:
                        for record in body.get("Records", []):
                            mark_failed(record["s3"]["object"]["key"])
                    except Exception as mark_err:
                        print(f"Could not mark failed: {mark_err}")


if __name__ == "__main__":
    main()