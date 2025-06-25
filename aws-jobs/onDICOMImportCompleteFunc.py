import json
import boto3
import os

sqs = boto3.client('sqs')
QUEUE_URL = os.environ['SQS_QUEUE_URL']  # Set in environment variables

def lambda_handler(event, context):
    print("Received Event:", json.dumps(event))

    try:
        detail = event.get('detail', {})
        job_status = detail.get('jobStatus')

        if job_status != 'COMPLETED':
            print(f"Job status is not COMPLETED: {job_status}")
            return

        metadata = {
            "jobId": detail.get("jobId"),
            "datastoreId": detail.get("datastoreId"),
            "inputS3Uri": detail.get("inputS3Uri"),
            "outputS3Uri": detail.get("outputS3Uri")
        }

        # Send metadata to SQS
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(metadata)
        )

        print("Metadata pushed to SQS:", metadata)
        print("SQS Response:", response)

    except Exception as e:
        print("Error processing event:", str(e))
        raise e
