import boto3
import urllib.parse
import os

healthimaging = boto3.client('medical-imaging')

DATASTORE_ID = os.environ['DATASTORE_ID']
INPUT_BUCKET = os.environ['INPUT_BUCKET']
OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
HEALTHIMAGING_ROLE_ARN = os.environ['HEALTHIMAGING_ROLE_ARN']

def lambda_handler(event, context):
    print("Event received:", event)
    
    for record in event['Records']:
        s3_object_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        
        if not s3_object_key.lower().endswith(".dcm"):
            print(f"Skipped non-DICOM file: {s3_object_key}")
            continue

        key_parts = s3_object_key.split('/')
        if len(key_parts) < 2:
            print("Unexpected key format. Skipping:", s3_object_key)
            continue

        study_prefix = '/'.join(key_parts[:2])  # e.g., dicom-import-folder/1.2.276...

        input_uri = f's3://{INPUT_BUCKET}/{study_prefix}/'
        print(f"Importing study from folder: {input_uri}")

        try:
            response = healthimaging.start_dicom_import_job(
                datastoreId=DATASTORE_ID,
                inputS3Uri=input_uri,
                outputS3Uri=f's3://{OUTPUT_BUCKET}/',
                dataAccessRoleArn=os.environ['HEALTHIMAGING_ROLE_ARN']
            )
            print("Successfully started import job:", response['jobId'])
        except Exception as e:
            print("Error starting import job:", e)
            raise e
