from fastapi import APIRouter, UploadFile, File as FastFile, Depends
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