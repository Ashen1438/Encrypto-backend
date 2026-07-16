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
from fastapi.responses import FileResponse
from app.models.user import User


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
    attempted_email: str | None = Form(None),
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

    resolved_user_id = user_id

    if resolved_user_id is None and attempted_email:
        matched_user = (
            db.query(User)
            .filter(User.email == attempted_email.strip().lower())
            .first()
        )

        if matched_user:
            resolved_user_id = matched_user.id

    incident = SecurityIncident(
        user_id=resolved_user_id,
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

@router.get("/incidents")
def list_security_incidents(
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(SecurityIncident)

    if user_id is not None:
        query = query.filter(
            SecurityIncident.user_id == user_id
        )

    incidents = (
        query
        .order_by(SecurityIncident.created_at.desc())
        .all()
    )

    return {
        "count": len(incidents),
        "incidents": [
            {
                "id": incident.id,
                "user_id": incident.user_id,
                "incident_type": incident.incident_type,
                "reason": incident.reason,
                "device_info": incident.device_info,
                "ip_address": incident.ip_address,
                "image_available": incident.image_path is not None,
                "image_url": (
                    f"/security/incidents/{incident.id}/image"
                    if incident.image_path
                    else None
                ),
                "created_at": incident.created_at,
            }
            for incident in incidents
        ],
    }
@router.get("/incidents/{incident_id}/image")
def get_security_incident_image(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(SecurityIncident)
        .filter(SecurityIncident.id == incident_id)
        .first()
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Security incident not found",
        )

    if not incident.image_path:
        raise HTTPException(
            status_code=404,
            detail="No image recorded for this incident",
        )

    if not os.path.exists(incident.image_path):
        raise HTTPException(
            status_code=404,
            detail="Incident image file not found",
        )

    return FileResponse(
        path=incident.image_path,
        media_type="image/jpeg",
        filename=os.path.basename(incident.image_path),
    )
    