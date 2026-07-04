import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

bucket = "docmind-documents"
uploads = s3.list_multipart_uploads(Bucket=bucket).get("Uploads", [])

for u in uploads:
    s3.abort_multipart_upload(Bucket=bucket, Key=u["Key"], UploadId=u["UploadId"])
    print(f"aborted {u['Key']}")

print(f"done — aborted {len(uploads)} uploads")