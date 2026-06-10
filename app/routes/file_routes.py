from fastapi import APIRouter, UploadFile, File as FastFile, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import shutil
import os
import uuid

from app.database import get_db
from app.models.file import File

router = APIRouter(prefix="/files", tags=["Files"])

UPLOAD_DIR = "uploads"

@router.post("/upload")
def upload_file(
    file: UploadFile = FastFile(...),
    db: Session = Depends(get_db)
):
    # unique file name
    unique_name = str(uuid.uuid4()) + "_" + file.filename
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_file = File(
        user_id=1,  # TEMP (later JWT use karamu)
        original_filename=file.filename,
        stored_filename=unique_name,
        file_path=file_path
    )

    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return {
        "message": "File uploaded",
        "file_id": new_file.id
    }

@router.get("/download/{file_id}")
def download_file(
    file_id: int,
    type: str = "original",
    db: Session = Depends(get_db)
):
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if type == "encrypted":
        path = file.encrypted_path
    elif type == "decrypted":
        path = file.decrypted_path
    else:
        path = file.file_path

    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File path does not exist on server")

    filename = file.original_filename
    if type == "encrypted":
        filename = "enc_" + filename
    elif type == "decrypted":
        filename = "dec_" + filename

    return FileResponse(
        path=path,
        filename=filename,
        media_type="application/octet-stream"
    )