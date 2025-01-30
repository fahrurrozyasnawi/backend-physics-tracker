import os
import shutil
from typing import Union
from typing_extensions import Annotated

from config.upload_dir import get_static_dir
from fastapi import APIRouter, UploadFile, File, Path
from models.api import CustomResponse

router = APIRouter(
    prefix='/upload',
    tags=['upload'],
    # redirect_slashes=False,
    responses={404: {"description": "Not Found"}}
)


@router.post('{path:path}', response_model=CustomResponse)
async def upload_file(
        path: str,
        file: Annotated[UploadFile, File(...)]):

    if not file:
        return CustomResponse(success=False, message='No Upload File')
    else:
        file_path = os.path.join(get_static_dir(), file.filename)
        if (path is not None):
            file_path = os.path.join(get_static_dir(), path[1:], file.filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        data = {"filename": file.filename, "path": path}
        return CustomResponse(success=True, message='Uploaded successfull', data=data)
