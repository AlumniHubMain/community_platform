"""Persistent storage client"""

from app.transport.persistent_storage.google.cloud_storage import CloudStorageAdapter


class PSClient:
    """Persistent storage client"""

    def __init__(
        self,
    ):
        self.adapter = None

    async def put_file(self, local_path: str, bucket_name: str, destination_path: str):
        """Put file to persistent"""
        result = await self.adapter.put_file(local_path, bucket_name, destination_path)
        return result

    async def put_file_bytes(self, file_bytes: bytes, bucket_name: str, destination_path: str):
        """Put file to persistent"""
        result = await self.adapter.put_file_bytes(file_bytes, bucket_name, destination_path)
        return result

    async def get_file(self, bucket_name: str, source_path: str, local_path: str):
        """Get file from persistent"""
        result = await self.adapter.get_file(bucket_name, source_path, local_path)
        return result

    async def initialize(self, adapter: CloudStorageAdapter):
        """Async init"""
        self.adapter = adapter
