import os
import tempfile
import boto3

from config import AWS_ENDPOINT, AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY

s3 = boto3.client(
    "s3",
    endpoint_url=AWS_ENDPOINT,
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

def download_to_temp(bucket, key):
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    s3.download_file(bucket, key, path)
    return path