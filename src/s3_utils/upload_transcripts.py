import os
import boto3
from src.utils.logger_setup import logger
import mimetypes

REGION = os.getenv("BACKBLAZE_REGION")
S3_ENDPOINT = os.getenv("BACKBLAZE_ENDPOINT")
S3_ACCESS_KEY = os.getenv("BACKBLAZE_KEY_ID")
S3_SECRET_KEY = os.getenv("BACKBLAZE_API_KEY")
BUCKET_NAME = os.getenv("BACKBLAZE_BUCKET_NAME")
CDN_BASE_URL = os.getenv("BACKBLAZE_CDN_URL")

# Initialize S3 client for DigitalOcean Spaces
try:
    s3_client = boto3.client('s3',
                            region_name=REGION,
                            endpoint_url=S3_ENDPOINT,
                            aws_access_key_id=S3_ACCESS_KEY,
                            aws_secret_access_key=S3_SECRET_KEY)
except Exception as e:
    logger.error(f"Error initializing S3 client::{e}")
    raise Exception("Could not initialize S3 client")


def upload_directory_to_bucket(source_directory, target_directory):
    """
    Uploads all files from the source directory to the target directory in the bucket.
    
    :param source_directory: The local directory to upload files from.
    :param target_directory: The target directory in the bucket.
    """
    for root, _, files in os.walk(source_directory):
        for file in files:
            src_filename = os.path.join(root, file)
            dest_filename = os.path.join(target_directory, os.path.relpath(src_filename, source_directory))
            print(f"Uploading {src_filename} to {dest_filename}")
            upload_file_to_bucket(src_filename, dest_filename)


def upload_file_to_bucket(src_filename, dest_filename, bucket_name=BUCKET_NAME, **kwargs):
    """
    :param spaces_client: Spaces client
    :param bucket_name: Unique name of space
    :param file_src: File location on disk
    :param save_as: Where to save file in the space
    :param kwargs
    :return:
    """
    logger.info(f"Uploading file to S3, bucket_name::{bucket_name}, file_src::{src_filename}, save_as::{dest_filename}")

    is_public = kwargs.get("is_public", False)
    content_type = kwargs.get("content_type")
    meta = kwargs.get("meta")

    if not content_type:
        file_type_guess = mimetypes.guess_type(src_filename)

        if not file_type_guess[0]:
            logger.error(f"Can't identify content type for file {src_filename}")
            raise Exception("Can't identify content type. Please specify directly via content_type arg.")

        content_type = file_type_guess[0]

    extra_args = {
        'ACL': "public-read" if is_public else "private",
        'ContentType': content_type
    }

    if isinstance(meta, dict):
        extra_args["Metadata"] = meta
    try:
        return s3_client.upload_file(
            src_filename,
            bucket_name,
            dest_filename,
            ExtraArgs=extra_args
        )
    except Exception as e:
        raise Exception(f"Error uploading file to S3::{e}")

