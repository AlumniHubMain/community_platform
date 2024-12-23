from fastapi import (
    APIRouter,
    UploadFile,
)

from .s3_proxy import gcs_client
from .schemas import AvatarData


router = APIRouter(tags=["Media data storage"], prefix="/mds")

summary = """
Uploads avatar into S3 storage
Supported formats are: jpeg/jpg, png
1. Calcs hash of file, filename and timestamp of now
2. Uploads original into <hash>/orig.<extension>
3. Converts original file into webp format and uploads it inti <hash>/webp.webp
4. Returns link to webp image
"""


@router.post("/upload", summary=summary)
async def upload_avatar(file: UploadFile) -> AvatarData:
    return await gcs_client.upload_avatar(file)
