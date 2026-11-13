import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from backend.app.config import settings

class ObjectStore:
    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        self.client = None
        self.is_s3 = False
        
        if settings.S3_ACCESS_KEY and settings.S3_SECRET_KEY and settings.S3_BUCKET_NAME:
            # Supabase Storage S3-compatible endpoints require signature_version='s3v4'
            # and path-style addressing (s3_force_path_style=True)
            self.client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL if settings.S3_ENDPOINT_URL else None,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"}
                )
            )
            self.is_s3 = True
        elif settings.APP_ENV == "production":
            raise RuntimeError("Production requires valid S3 credentials and bucket name.")
            
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
        if self.is_s3 and self.client:
            self.client.put_object(
                Bucket=self.bucket,
                Key=storage_key,
                Body=data,
                ContentType="application/pdf"
            )
            return f"s3://{self.bucket}/{storage_key}"
        elif settings.APP_ENV == "production":
            raise RuntimeError("Cannot store PDF: S3 object store not configured in production mode.")
        else:
            # Dev / Serverless local disk storage (in Vercel, only /tmp is writable)
            default_storage = "/tmp/storage" if os.environ.get("VERCEL") else os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "storage")
            local_dir = default_storage
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, storage_key.replace("/", "_"))
            with open(local_path, "wb") as f:
                f.write(data)
            return local_path

    def get_pdf(self, storage_key: str) -> bytes:
        if self.is_s3 and self.client:
            resp = self.client.get_object(Bucket=self.bucket, Key=storage_key)
            return resp["Body"].read()
        elif settings.APP_ENV == "production":
            raise RuntimeError("Cannot retrieve PDF: S3 object store not configured in production mode.")
        else:
            default_storage = "/tmp/storage" if os.environ.get("VERCEL") else os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "storage")
            local_dir = default_storage
            local_path = os.path.join(local_dir, storage_key.replace("/", "_"))
            if not os.path.exists(local_path) and os.path.exists(storage_key):
                local_path = storage_key
            with open(local_path, "rb") as f:
                return f.read()

object_store = ObjectStore()
