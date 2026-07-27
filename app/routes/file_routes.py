from fastapi import APIRouter, UploadFile, File as FastFile, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import shutil
import os
import uuid

from app.database import get_db
from app.models.file import File

from app.models.user import User
from app.utils.auth_dependency import get_current_user

router = APIRouter(prefix="/files", tags=["Files"])

UPLOAD_DIR = "uploads"

@router.post("/upload")
def upload_file(
    file: UploadFile = FastFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # unique file name
    unique_name = str(uuid.uuid4()) + "_" + file.filename
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_file = File(
        user_id=current_user.id,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = (
    db.query(File)
    .filter(
        File.id == file_id,
        File.user_id == current_user.id,
    )
    .first()
)
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


@router.get("/dashboard")
def get_vault_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base_query = db.query(File).filter(
    File.user_id == current_user.id
)

    encrypted_files = base_query.filter(
        File.encrypted_path.isnot(None)
    ).count()

    protected_sessions = base_query.filter(
        File.protection_mode.isnot(None)
    ).count()

    recent_records = (
        base_query
        .order_by(File.created_at.desc())
        .limit(10)
        .all()
    )

    recent_files = []

    for file_record in recent_records:
        available_path = None

        possible_paths = [
            file_record.decrypted_path,
            file_record.encrypted_path,
            file_record.file_path,
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                available_path = path
                break

        size_bytes = None

        if available_path:
            try:
                size_bytes = os.path.getsize(available_path)
            except OSError:
                size_bytes = None

        recent_files.append({
            "file_id": file_record.id,
            "name": file_record.original_filename,
            "status": file_record.status,
            "protection_mode": file_record.protection_mode,
            "size_bytes": size_bytes,
            "created_at": (
                file_record.created_at.isoformat()
                if file_record.created_at
                else None
            ),
        })

    return {
        "encrypted_files": encrypted_files,
        "cloud_synced": 0,
        "protected_sessions": protected_sessions,
        "recent_files": recent_files,
    }