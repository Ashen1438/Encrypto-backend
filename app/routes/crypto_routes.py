from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models.file import File
from app.services.encryption_service import generate_key, encrypt_file, decrypt_file

router = APIRouter(prefix="/crypto", tags=["Crypto"])


# 🔐 ENCRYPT
@router.post("/encrypt/{file_id}")
def encrypt_file_api(file_id: int, db: Session = Depends(get_db)):
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    key = generate_key()

    encrypted_path = os.path.join("encrypted", "enc_" + file.stored_filename)

    encrypt_file(file.file_path, encrypted_path, key)

    file.encrypted_path = encrypted_path
    file.status = "encrypted"

    db.commit()

    return {
        "message": "File encrypted",
        "key": key.decode()
    }

@router.post("/decrypt/{file_id}")
def decrypt_file_api(file_id: int, key: str, db: Session = Depends(get_db)):
    file = db.query(File).filter(File.id == file_id).first()

    if not file or not file.encrypted_path:
        raise HTTPException(status_code=404, detail="Encrypted file not found")

    decrypted_filename = "dec_" + file.stored_filename
    decrypted_path = os.path.join("decrypted", decrypted_filename)

    decrypt_file(file.encrypted_path, decrypted_path, key.encode())

    file.decrypted_path = decrypted_path
    file.status = "decrypted"

    db.commit()

    return {
        "message": "File decrypted"
    }