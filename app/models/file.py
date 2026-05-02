from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)

    file_path = Column(String)
    encrypted_path = Column(String)
    decrypted_path = Column(String)

    status = Column(String, default="uploaded")

    created_at = Column(DateTime, default=datetime.utcnow)