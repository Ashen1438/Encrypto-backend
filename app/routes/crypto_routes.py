from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import os

from app.database import get_db
from app.models.file import File
from app.services.encryption_service import (
    decrypt_file,
    decrypt_file_with_password,
    encrypt_file,
    encrypt_file_with_password,
    generate_key,
)


router = APIRouter(prefix="/crypto", tags=["Crypto"])


class PasswordRequest(BaseModel):
    password: str = Field(min_length=6, max_length=128)
    mode: str


def get_file_or_404(
    file_id: int,
    db: Session,
) -> File:
    file_record = db.query(File).filter(File.id == file_id).first()

    if not file_record:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return file_record


def get_encrypted_input_path(file_record: File) -> str:
    input_path = (
        file_record.encrypted_path
        if file_record.encrypted_path
        else file_record.file_path
    )

    if not input_path or not os.path.exists(input_path):
        raise HTTPException(
            status_code=404,
            detail="Encrypted file not found",
        )

    return input_path


# =========================================================
# PERSONAL MODE - BIOMETRIC / AUTO GENERATED KEY
# =========================================================

@router.post("/encrypt/{file_id}")
def encrypt_file_api(
    file_id: int,
    db: Session = Depends(get_db),
):
    file_record = get_file_or_404(file_id, db)

    if not file_record.file_path or not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=404,
            detail="Original file not found",
        )

    os.makedirs("encrypted", exist_ok=True)

    key = generate_key()

    encrypted_filename = "enc_" + file_record.stored_filename
    encrypted_path = os.path.join(
        "encrypted",
        encrypted_filename,
    )

    try:
        encrypt_file(
            input_path=file_record.file_path,
            output_path=encrypted_path,
            key=key,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Encryption failed: {error}",
        ) from error

    file_record.encrypted_path = encrypted_path
    file_record.status = "encrypted"
    file_record.protection_mode = "biometric"

    db.commit()
    db.refresh(file_record)

    return {
        "message": "File encrypted",
        "mode": "biometric",
        "file_id": file_record.id,
        "key": key.decode("utf-8"),
    }


@router.post("/decrypt/{file_id}")
def decrypt_file_api(
    file_id: int,
    key: str,
    db: Session = Depends(get_db),
):
    file_record = get_file_or_404(file_id, db)

    input_path = get_encrypted_input_path(file_record)

    os.makedirs("decrypted", exist_ok=True)

    decrypted_filename = "dec_" + file_record.stored_filename
    decrypted_path = os.path.join(
        "decrypted",
        decrypted_filename,
    )

    try:
        decrypt_file(
            input_path=input_path,
            output_path=decrypted_path,
            key=key.encode("utf-8"),
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid decryption key or corrupted file",
        ) from error

    file_record.decrypted_path = decrypted_path
    file_record.status = "decrypted"

    db.commit()
    db.refresh(file_record)

    return {
        "message": "File decrypted",
        "mode": "biometric",
        "file_id": file_record.id,
        "decrypted_path": decrypted_path,
    }


# =========================================================
# SHARE MODE - PASSWORD BASED
# =========================================================

@router.post("/encrypt-password/{file_id}")
def encrypt_file_with_password_api(
    file_id: int,
    data: PasswordRequest,
    db: Session = Depends(get_db),
):
    file_record = get_file_or_404(file_id, db)

    if data.mode not in ["hybrid", "password_only"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid protection mode",
        )

    if not file_record.file_path or not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=404,
            detail="Original file not found",
        )

    os.makedirs("encrypted", exist_ok=True)

    encrypted_filename = "enc_" + file_record.stored_filename
    encrypted_path = os.path.join(
        "encrypted",
        encrypted_filename,
    )

    try:
        encrypt_file_with_password(
    input_path=file_record.file_path,
    output_path=encrypted_path,
    password=data.password,
    mode=data.mode,
)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Password encryption failed: {error}",
        ) from error

    file_record.encrypted_path = encrypted_path
    file_record.status = "password_encrypted"
    file_record.protection_mode = data.mode

    db.commit()
    db.refresh(file_record)

    return {
        "message": "File encrypted with password protection",
        "mode": data.mode,
        "file_id": file_record.id,
    }

@router.post("/decrypt-password/{file_id}")
def decrypt_file_with_password_api(
    file_id: int,
    data: PasswordRequest,
    db: Session = Depends(get_db),
):
    file_record = get_file_or_404(file_id, db)

    if data.mode not in ["hybrid", "password_only"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid protection mode",
        )


    input_path = get_encrypted_input_path(file_record)

    os.makedirs("decrypted", exist_ok=True)

    decrypted_filename = "dec_" + file_record.stored_filename
    decrypted_path = os.path.join(
        "decrypted",
        decrypted_filename,
    )

    try:
        decrypt_file_with_password(
        input_path=input_path,
        output_path=decrypted_path,
        password=data.password,
        expected_mode=data.mode,
)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="Password decryption failed",
        ) from error

    file_record.decrypted_path = decrypted_path
    file_record.status = "password_decrypted"
    file_record.protection_mode = data.mode

    db.commit()
    db.refresh(file_record)

    return {
        "message": "File decrypted with password protection",
        "mode": data.mode,
        "file_id": file_record.id,
        "decrypted_path": decrypted_path,
    }