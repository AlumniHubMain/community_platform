import aiohttp
from gcloud.aio.storage import Storage  # pip install gcloud-aio-storage
from google.oauth2 import service_account  # pip install google-auth
from common_db import settings
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from typing import Literal
from datetime import datetime


class GCSClient:
    def __init__(self):
        self._credentials = service_account.Credentials.from_service_account_file(
            settings.google_application_credentials
        )
        self._bucket_name = settings.google_cloud_bucket
        self._supported_extensions = ("jpg", "jpeg", "gif")

    async def upload_file(self, file) -> str:
        async with aiohttp.ClientSession() as session:
            client = Storage(session=session)

            # Extract filename and extension
            original_filename = file.filename
            name, extension = original_filename.rsplit('.', 1) if '.' in original_filename else (original_filename, '')
            if extension not in self._supported_extensions:
                raise Exception("Unsupported image extension")

            # Generate timestamp in the format YYYYMMDDHH
            timestamp = datetime.now().strftime('%Y%m%d%H')
            # Create new filename with timestamp
            new_filename = f"{name}_{timestamp}.{extension}" if extension else f"{name}_{timestamp}"

            blob_name = f"{folder}/{entity_id}/{subfolder}/{new_filename}"
            await client.upload(self._bucket_name, blob_name, file.file)

            return f"{blob_name}"

    # async def download_file(self, blob: str, output_type: Literal["stream", "bytes"] = "stream") \
    #         -> StreamingResponse | bytes:
    #     """
    #     Выгрузка файлов из GCloud Storage по пути (blob). Нет проверок на легитимность операции скачивания.
    #     НЕ ПРЕДОСТАВЛЯТЬ прямой доступ пользователям к переменной blob.
    #     В пользовательских эндпоинтах идет перепроверка ../me/.., так что чужие файлы не удастся скачать.
    #     blob = f"{folder}/{entity_id}/{subfolder}/{filename}"
    #     Возвращает StreamingResponse (например, для web) или Bytes (например, для attachments в емейл)
    #     """
    #     async with aiohttp.ClientSession() as session:
    #         client = Storage(session=session)
    #         try:
    #             content = await client.download(self._bucket_name, blob)
    #
    #             # Ensure the content is in bytes
    #             if not isinstance(content, bytes):
    #                 raise HTTPException(status_code=500, detail="File content is not in bytes format.")
    #
    #             if output_type == "bytes":
    #                 return content
    #
    #             # Create a BytesIO stream from the content
    #             file_stream = BytesIO(content)
    #             # Create a StreamingResponse with appropriate headers
    #             response = StreamingResponse(file_stream, media_type='application/octet-stream')
    #             response.headers["Content-Disposition"] = f"attachment; filename={blob.split('/')[-1]}"
    #
    #         except aiohttp.ClientResponseError as e:
    #             raise HTTPException(status_code=e.status, detail=f"Error downloading file")
    #
    #         except Exception as e:
    #             raise HTTPException(status_code=500, detail=f"An unexpected error occurred")
    #
    #         return response


gcs_client = GCSClient()  # Инициализация клиента Google Cloud Storage