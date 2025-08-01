import os
from dotenv import load_dotenv
import boto3

# Load .env file
load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Environment variables
AWS_REGION = os.getenv("AWS_DEFAULT_REGION")
AWS_PROFILE = os.getenv("AWS_PROFILE")
DICOM_IMPORT_QUEUE_URL = os.getenv("SQS_DICOM_IMPORT_QUEUE_URL")
OCR_UPLOAD_QUEUE_URL = os.getenv("SQS_OCR_UPLOAD_QUEUE_URL")
DATASTORE_ID = os.getenv("DATASTORE_ID")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME")
DATASTORE_ID = os.getenv("DATASTORE_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# AWS session
session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)

# Clients and resources
sqs = session.client('sqs')
healthimaging = session.client('medical-imaging')
dynamodb = session.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)
s3 = session.client("s3")