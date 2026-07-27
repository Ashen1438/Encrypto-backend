from fastapi import (
    APIRouter,
    Depends,
    File as FastFile,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse

import os
import uuid

from app.models.user import User
from app.utils.auth_dependency import (
    get_current_user,
)


router = APIRouter(
    prefix="/stego",
    tags=["Steganography"],
)

STEGO_DIR = "stego"
os.makedirs(STEGO_DIR, exist_ok=True)

MARKER = b"---ENCRYPTO_STEGO_DATA---"


def get_user_stego_directory(
    user_id: int,
) -> str:
    user_directory = os.path.join(
        STEGO_DIR,
        str(user_id),
    )

    os.makedirs(
        user_directory,
        exist_ok=True,
    )

    return user_directory


@router.post("/hide")
def hide_file_in_image(
    cover_image: UploadFile = FastFile(...),
    hidden_file: UploadFile = FastFile(...),
    current_user: User = Depends(
        get_current_user
    ),
):
    cover_filename = (
        cover_image.filename or ""
    )

    cover_ext = os.path.splitext(
        cover_filename
    )[1].lower()

    if cover_ext not in [
        ".png",
        ".jpg",
        ".jpeg",
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cover file must be PNG "
                "or JPG image"
            ),
        )

    hidden_filename = os.path.basename(
        hidden_file.filename
        or "hidden_file"
    )

    user_directory = (
        get_user_stego_directory(
            current_user.id
        )
    )

    output_name = (
        f"stego_{uuid.uuid4()}"
        f"{cover_ext}"
    )

    output_path = os.path.join(
        user_directory,
        output_name,
    )

    cover_bytes = cover_image.file.read()
    hidden_bytes = hidden_file.file.read()

    with open(output_path, "wb") as output_file:
        output_file.write(cover_bytes)
        output_file.write(MARKER)
        output_file.write(
            hidden_filename.encode(
                "utf-8"
            )
        )
        output_file.write(MARKER)
        output_file.write(hidden_bytes)

    return {
        "message":
            "Data hidden inside image successfully",
        "stego_filename": output_name,
        "download_url":
            f"/stego/download/{output_name}",
    }


@router.post("/extract")
def extract_file_from_image(
    stego_image: UploadFile = FastFile(...),
    current_user: User = Depends(
        get_current_user
    ),
):
    data = stego_image.file.read()

    parts = data.split(
        MARKER,
        2,
    )

    if len(parts) != 3:
        raise HTTPException(
            status_code=400,
            detail=(
                "No hidden data found "
                "in this image"
            ),
        )

    hidden_filename = os.path.basename(
        parts[1].decode(
            "utf-8",
            errors="ignore",
        )
        or "hidden_file"
    )

    hidden_data = parts[2]

    user_directory = (
        get_user_stego_directory(
            current_user.id
        )
    )

    output_name = (
        f"extracted_{uuid.uuid4()}_"
        f"{hidden_filename}"
    )

    output_path = os.path.join(
        user_directory,
        output_name,
    )

    with open(output_path, "wb") as output_file:
        output_file.write(hidden_data)

    return {
        "message":
            "Hidden file extracted successfully",
        "extracted_filename": output_name,
        "download_url":
            f"/stego/download/{output_name}",
    }


@router.get("/download/{filename}")
def download_stego_file(
    filename: str,
    current_user: User = Depends(
        get_current_user
    ),
):
    safe_filename = os.path.basename(
        filename
    )

    if (
        safe_filename != filename
        or "/" in filename
        or "\\" in filename
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename",
        )

    user_directory = (
        get_user_stego_directory(
            current_user.id
        )
    )

    path = os.path.join(
        user_directory,
        safe_filename,
    )

    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return FileResponse(
        path=path,
        filename=safe_filename,
        media_type=(
            "application/octet-stream"
        ),
    )