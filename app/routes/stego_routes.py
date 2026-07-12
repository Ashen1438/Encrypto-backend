from fastapi import APIRouter, UploadFile, File as FastFile, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
import shutil

router = APIRouter(prefix="/stego", tags=["Steganography"])

STEGO_DIR = "stego"
os.makedirs(STEGO_DIR, exist_ok=True)

MARKER = b"---ENCRYPTO_STEGO_DATA---"


@router.post("/hide")
def hide_file_in_image(
    cover_image: UploadFile = FastFile(...),
    hidden_file: UploadFile = FastFile(...)
):
    cover_ext = os.path.splitext(cover_image.filename)[1].lower()

    if cover_ext not in [".png", ".jpg", ".jpeg"]:
        raise HTTPException(status_code=400, detail="Cover file must be PNG or JPG image")

    output_name = f"stego_{uuid.uuid4()}{cover_ext}"
    output_path = os.path.join(STEGO_DIR, output_name)

    cover_bytes = cover_image.file.read()
    hidden_bytes = hidden_file.file.read()

    with open(output_path, "wb") as f:
        f.write(cover_bytes)
        f.write(MARKER)
        f.write(hidden_file.filename.encode("utf-8"))
        f.write(MARKER)
        f.write(hidden_bytes)

    return {
        "message": "Data hidden inside image successfully",
        "stego_filename": output_name,
        "download_url": f"/stego/download/{output_name}"
    }


@router.post("/extract")
def extract_file_from_image(
    stego_image: UploadFile = FastFile(...)
):
    data = stego_image.file.read()

    parts = data.split(MARKER)

    if len(parts) < 3:
        raise HTTPException(status_code=400, detail="No hidden data found in this image")

    hidden_filename = parts[1].decode("utf-8", errors="ignore")
    hidden_data = parts[2]

    output_name = f"extracted_{uuid.uuid4()}_{hidden_filename}"
    output_path = os.path.join(STEGO_DIR, output_name)

    with open(output_path, "wb") as f:
        f.write(hidden_data)

    return {
        "message": "Hidden file extracted successfully",
        "extracted_filename": output_name,
        "download_url": f"/stego/download/{output_name}"
    }


@router.get("/download/{filename}")
def download_stego_file(filename: str):
    path = os.path.join(STEGO_DIR, filename)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=path,
        filename=filename,
        media_type="application/octet-stream"
    )