import os
import boto3
from botocore.exceptions import ClientError
from backend.app.config import settings

class ObjectStore:
    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        self.client = None
        # Check if remote S3 / Supabase Storage credentials are provided
        if settings.S3_ACCESS_KEY and settings.S3_SECRET_KEY:
            self.client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL if settings.S3_ENDPOINT_URL else None,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION
            )
            
    def ensure_bucket(self):
        if not self.client:
            return
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket)
            except Exception as e:
                pass

    def upload_pdf(self, storage_key: str, data: bytes) -> str:
        if self.client:
            try:
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=storage_key,
                    Body=data,
                    ContentType="application/pdf"
                )
                return f"s3://{self.bucket}/{storage_key}"
            except Exception:
                # Fallback to local durable directory if S3 endpoint is unavailable
                pass
                
        local_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "storage")
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, storage_key.replace("/", "_"))
        with open(local_path, "wb") as f:
            f.write(data)
        return local_path

    def get_pdf(self, storage_key: str) -> bytes:
        if self.client:
            try:
                resp = self.client.get_object(Bucket=self.bucket, Key=storage_key)
                return resp["Body"].read()
            except Exception:
                pass
                
        local_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "storage")
        local_path = os.path.join(local_dir, storage_key.replace("/", "_"))
        with open(local_path, "rb") as f:
            return f.read()

object_store = ObjectStore()
