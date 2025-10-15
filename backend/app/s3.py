"""
S3/MinIO client utilities
"""
import hashlib
import io
from typing import Optional, BinaryIO, Tuple
from urllib.parse import urlparse
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings


class S3Client:
    """S3/MinIO client wrapper"""

    def __init__(self):
        """Initialize S3 client"""
        # Parse endpoint to determine if using path style
        endpoint_url = settings.s3_endpoint

        # Create boto3 client
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path' if settings.s3_force_path_style else 'auto'}
            ),
            use_ssl=settings.s3_secure
        )
        self.bucket = settings.s3_bucket

    def ensure_bucket_exists(self) -> None:
        """
        Ensure bucket exists, create if not
        """
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if settings.s3_region == 'us-east-1':
                        self.client.create_bucket(Bucket=self.bucket)
                    else:
                        self.client.create_bucket(
                            Bucket=self.bucket,
                            CreateBucketConfiguration={'LocationConstraint': settings.s3_region}
                        )
                except ClientError as create_error:
                    raise Exception(f"Failed to create bucket: {create_error}")
            else:
                raise Exception(f"Failed to check bucket: {e}")

    def upload_file(
        self,
        file_obj: BinaryIO,
        object_key: str,
        content_type: str = "application/octet-stream"
    ) -> Tuple[str, int]:
        """
        Upload file to S3 and return SHA256 hash and size

        Args:
            file_obj: File-like object to upload
            object_key: S3 object key
            content_type: MIME type

        Returns:
            Tuple of (sha256_hash, size_in_bytes)
        """
        # Read file content
        file_content = file_obj.read()
        file_size = len(file_content)

        # Calculate SHA256
        sha256_hash = hashlib.sha256(file_content).hexdigest()

        # Reset file pointer
        file_obj.seek(0)

        # Upload to S3
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'sha256': sha256_hash,
                    'original-size': str(file_size)
                }
            )
        except ClientError as e:
            raise Exception(f"Failed to upload to S3: {e}")

        return sha256_hash, file_size

    def download_file(self, object_key: str) -> bytes:
        """
        Download file from S3

        Args:
            object_key: S3 object key

        Returns:
            File content as bytes
        """
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=object_key)
            return response['Body'].read()
        except ClientError as e:
            raise Exception(f"Failed to download from S3: {e}")

    def stream_file(self, object_key: str):
        """
        Stream file from S3

        Args:
            object_key: S3 object key

        Returns:
            Streaming body object
        """
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=object_key)
            return response['Body']
        except ClientError as e:
            raise Exception(f"Failed to stream from S3: {e}")

    def get_file_metadata(self, object_key: str) -> dict:
        """
        Get file metadata from S3

        Args:
            object_key: S3 object key

        Returns:
            Metadata dict
        """
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=object_key)
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {}),
                'etag': response.get('ETag', '').strip('"')
            }
        except ClientError as e:
            raise Exception(f"Failed to get metadata from S3: {e}")

    def file_exists(self, object_key: str) -> bool:
        """
        Check if file exists in S3

        Args:
            object_key: S3 object key

        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                return False
            raise Exception(f"Failed to check file existence: {e}")

    def delete_file(self, object_key: str) -> None:
        """
        Delete file from S3

        Args:
            object_key: S3 object key
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_key)
        except ClientError as e:
            raise Exception(f"Failed to delete from S3: {e}")

    def generate_presigned_url(
        self,
        object_key: str,
        expiration: int = 3600,
        http_method: str = 'GET'
    ) -> str:
        """
        Generate presigned URL for S3 object

        Args:
            object_key: S3 object key
            expiration: URL expiration time in seconds
            http_method: HTTP method (GET, PUT, etc.)

        Returns:
            Presigned URL
        """
        try:
            if http_method == 'GET':
                url = self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': object_key},
                    ExpiresIn=expiration
                )
            else:
                url = self.client.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': self.bucket, 'Key': object_key},
                    ExpiresIn=expiration
                )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {e}")

    def get_bucket_size(self) -> int:
        """
        Calculate total size of all objects in bucket

        Returns:
            Total size in bytes
        """
        try:
            total_size = 0
            paginator = self.client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_size += obj['Size']
            return total_size
        except ClientError as e:
            raise Exception(f"Failed to get bucket size: {e}")


# Global S3 client instance
s3_client = S3Client()


def calculate_sha256(file_obj: BinaryIO) -> str:
    """
    Calculate SHA256 hash of file

    Args:
        file_obj: File-like object

    Returns:
        SHA256 hash as hex string
    """
    sha256_hash = hashlib.sha256()
    file_obj.seek(0)

    # Read in chunks to handle large files
    for chunk in iter(lambda: file_obj.read(8192), b""):
        sha256_hash.update(chunk)

    file_obj.seek(0)
    return sha256_hash.hexdigest()


def generate_s3_key(
    package_identifier: str,
    version: str,
    architecture: str,
    filename: str
) -> str:
    """
    Generate S3 object key for installer

    Args:
        package_identifier: Package identifier (e.g., "7zip.7zip")
        version: Version string
        architecture: Architecture (x64, x86, etc.)
        filename: Original filename

    Returns:
        S3 object key
    """
    # Sanitize components
    safe_identifier = package_identifier.replace("/", "_").replace("\\", "_")
    safe_version = version.replace("/", "_").replace("\\", "_")
    safe_arch = architecture.replace("/", "_").replace("\\", "_")

    return f"{safe_identifier}/{safe_version}/{safe_arch}/{filename}"
