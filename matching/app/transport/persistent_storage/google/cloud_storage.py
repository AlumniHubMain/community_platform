"""Cloud storage adapter"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import aiofiles
from google.cloud import storage

from app.config import config
from app.persistent_storage.persistent_adapter import PersistentStorage


class CloudStorageAdapter(PersistentStorage):
    """Google Cloud Storage adapter"""

    def __init__(self):
        self.storage_client = None

    async def put_file(self, local_path: str, bucket_name: str, destination_path: str):
        async with aiofiles.open(local_path, "rb") as file:
            content = await file.read()
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_path)
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, blob.upload_from_string, content)
        return True

    async def put_file_bytes(self, file_bytes: bytes, bucket_name: str, destination_path: str):
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_path)
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, blob.upload_from_string, file_bytes)
        return True

    async def get_file(self, bucket_name: str, source_path: str, local_path: str):
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(source_path)
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            content = await loop.run_in_executor(executor, blob.download_as_string)
        async with aiofiles.open(local_path, "wb") as file:
            await file.write(content)
        return True

    async def initialize(self):
        self.storage_client = storage.Client(project=config.active_config.project_id)
