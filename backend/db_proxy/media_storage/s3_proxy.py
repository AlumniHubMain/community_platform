import aiohttp
from common_db import settings
from datetime import datetime
from fastapi import UploadFile
from gcloud.aio.storage import Storage
from hashlib import md5
from io import BytesIO
from PIL import Image


def make_hash(file: UploadFile) -> str:
    hash_calc = md5()
    hash_calc.update(file.filename.encode('utf-8'))
    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    hash_calc.update(timestamp.encode('utf-8'))
    return hash_calc.hexdigest()


def convert_into_webp(file: UploadFile) -> BytesIO:
    image = Image.open(BytesIO(file.file.read()))
    file.file.seek(0)
    result = BytesIO()
    image.save(result, 'webp')
    result.seek(0)
    return result

class GCSClient:
    def __init__(self):
        self._credentials_file = settings.google_application_credentials
        self._bucket_name = settings.google_cloud_bucket
        self._supported_extensions = ("jpg", "jpeg", "png")

    def check_file_extension(self, file: UploadFile) -> str:
        original_filename = file.filename
        name, extension = original_filename.rsplit('.', 1) if '.' in original_filename else (original_filename, '')
        extension = extension.lower()
        if extension not in self._supported_extensions:
            raise Exception("Unsupported image extension")
        return extension

    async def upload_avatar(self, file: UploadFile) -> dict:
        async with aiohttp.ClientSession() as session:
            client = Storage(session=session, service_file=self._credentials_file)
            extension = self.check_file_extension(file)
            dir_name = make_hash(file)

            orig_name = f"{dir_name}/orig.{extension}"
            webp_name = f"{dir_name}/webp.webp"
            webp_data = convert_into_webp(file)

            orig_status = await client.upload(self._bucket_name, orig_name, file.file.read())
            webp_status = await client.upload(self._bucket_name, webp_name, webp_data.read())

            # ToDo(evseev.dmsr): Extract media links from API
            result = {
                'orig': f'https://storage.googleapis.com/{self._bucket_name}/{orig_status['name']}',
                'webp': f'https://storage.googleapis.com/{self._bucket_name}/{webp_status['name']}'
            }
            return result


gcs_client = GCSClient()
