"""S3 like storage adapter"""

from abc import ABC, abstractmethod


class PersistentStorage(ABC):
    """Base class for persistent storages"""

    db_client: any
    config: any

    @abstractmethod
    async def put_file(self, local_path: str, bucket_name: str, destination_path: str): ...

    @abstractmethod
    async def put_file_bytes(self, file_bytes: bytes, bucket_name: str, destination_path: str): ...

    @abstractmethod
    async def get_file(self, bucket_name: str, source_path: str, local_path: str): ...

    @abstractmethod
    async def initialize(self): ...
