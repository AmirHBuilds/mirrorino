# backend/s3_utils.py
import boto3
import logging
from config import settings

# Setup basic logger for production
logger = logging.getLogger("uvicorn.error")

s3_client = boto3.client(
    's3',
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY
)

def upload_to_s3(file_obj, s3_key, content_type):
    try:
        s3_client.upload_fileobj(
            file_obj,
            settings.S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": content_type}
        )
        return True
    except Exception as e:
        logger.error(f"S3 Upload Error: {str(e)}")
        return False

def get_presigned_url(s3_key, is_raw=False):
    params = {'Bucket': settings.S3_BUCKET, 'Key': s3_key}
    if not is_raw:
        params['ResponseContentDisposition'] = 'attachment'
        
    return s3_client.generate_presigned_url('get_object', Params=params, ExpiresIn=3600)

def delete_from_s3(s3_key):
    try:
        s3_client.delete_object(Bucket=settings.S3_BUCKET, Key=s3_key)
    except Exception as e:
        logger.error(f"S3 Delete Error: {str(e)}")