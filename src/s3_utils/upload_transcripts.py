import os
import boto3
from src.utils.logger_setup import logger

SPACES_REGION = os.getenv("BACKBLAZE_REGION")
SPACES_ENDPOINT = os.getenv("BACKBLAZE_ENDPOINT")
SPACES_ACCESS_KEY = os.getenv("BACKBLAZE_KEY_ID")
SPACES_SECRET_KEY = os.getenv("BACKBLAZE_API_KEY")
SPACES_NAME = os.getenv("BACKBLAZE_BUCKET_NAME")
CDN_BASE_URL = os.getenv("BACKBLAZE_CDN_URL")

# Initialize S3 client for DigitalOcean Spaces
try:
    s3_client = boto3.client('s3',
                            region_name=SPACES_REGION,
                            endpoint_url=SPACES_ENDPOINT,
                            aws_access_key_id=SPACES_ACCESS_KEY,
                            aws_secret_access_key=SPACES_SECRET_KEY)
except Exception as e:
    logger.error(f"Error initializing S3 client::{e}")
    raise Exception("Could not initialize S3 client")


parent_key_path = f"training_data/transcripts"

import boto3
import mimetypes
from src.utils.logger_setup import logger


def upload_file_to_bucket(spaces_client, bucket_name, file_src, save_as, **kwargs):
    """
    :param spaces_client: Spaces client
    :param bucket_name: Unique name of space
    :param file_src: File location on disk
    :param save_as: Where to save file in the space
    :param kwargs
    :return:
    """
    logger.info(f"Uploading file to S3, bucket_name::{bucket_name}, file_src::{file_src}, save_as::{save_as}")

    is_public = kwargs.get("is_public", False)
    content_type = kwargs.get("content_type")
    meta = kwargs.get("meta")

    if not content_type:
        file_type_guess = mimetypes.guess_type(file_src)

        if not file_type_guess[0]:
            logger.error(f"Can't identify content type for file {file_src}")
            raise Exception("Can't identify content type. Please specify directly via content_type arg.")

        content_type = file_type_guess[0]

    extra_args = {
        'ACL': "public-read" if is_public else "private",
        'ContentType': content_type
    }

    if isinstance(meta, dict):
        extra_args["Metadata"] = meta

    return spaces_client.upload_file(
        file_src,
        bucket_name,
        save_as,
        ExtraArgs=extra_args
    )

