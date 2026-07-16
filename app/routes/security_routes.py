from fastapi import (
    APIRouter,
    Depends,
    File as FastFile,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from sqlalchemy.orm import Session

import os
import shutil
import uuid

from app.database import get_db
from app.models.security_incident import SecurityIncident


router = APIRouter(
    prefix="/security",
    tags=["Security"],
)

SECURITY_IMAGE_DIR = "security_incidents"
os.makedirs(SECURITY_IMAGE_DIR, exist_ok=True)


@router.post("/incidents")
def create_security_incident(
    request: Request,
    reason: str = Form(...),
    incident_type: str = Form("unauthorized_access"),
    device_info: str | None = Form(None),
    user_id: int | None = Form(None),
    image: UploadFile | None = FastFile(None),
    db: Session = Depends(get_db),
):
    image_path = None

    if image is not None:
        image_extension = os.path.splitext(
            image.filename or ""
        )[1].lower()

        if image_extension not in [
            ".jpg",
            ".jpeg",
            ".png",
        ]:
            raise HTTPException(
                status_code=400,
                detail="Incident image must be JPG or PNG",
            )

        stored_filename = (
            f"{uuid.uuid4()}{image_extension}"
        )

        image_path = os.path.join(
            SECURITY_IMAGE_DIR,
            stored_filename,
        )

        with open(image_path, "wb") as output_file:
            shutil.copyfileobj(
                image.file,
                output_file,
            )

    client_ip = None

    if request.client is not None:
        client_ip = request.client.host

    incident = SecurityIncident(
        user_id=user_id,
        incident_type=incident_type,
        reason=reason,
        image_path=image_path,
        device_info=device_info,
        ip_address=client_ip,
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return {
        "message": "Security incident recorded",
        "incident_id": incident.id,
        "incident_type": incident.incident_type,
        "reason": incident.reason,
        "image_available": image_path is not None,
        "created_at": incident.created_at,
    }