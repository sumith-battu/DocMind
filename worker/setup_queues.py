import json
import boto3

sqs = boto3.client("sqs",
    enpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

dlq_url = sqs.create_queue(QueueName="document-jobs-dlq")["QueueUrl"]
dlq_arn = sqs.get_queue_attributes(
    QueueUrl=dlq_url, AttributeNames=["QueueArn"]
)["Attributes"]["QueueArn"]

print("DLQ:", dlq_arn)

main_url = sqs.get_queue_url(QueueName="docmind-jobs")["QueueUrl"]
sqs.set_queue_attributes(
    QueueUrl=main_url,
    Attributes={
        "RedrivePolicy": json.dumps({
            "deadLetterTargetArn": dlq_arn,
            "maxReceiveCount": "3",
        }),
        "VisibilityTimeout": "900",
    },
)
print("Redrive policy + visibility timeout set on main queue")

