from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

import os
import re
import gc

import fitz
import joblib
import pandas as pd

from app.database import get_db
from app.models.file import File
from app.models.user import User
from app.utils.auth_dependency import get_current_user



MODEL_PATH = "app/ml/risk_model.pkl"

encoder = joblib.load(
    "app/ml/extension_encoder.pkl"
)

def extract_text_from_pdf(
    path: str,
) -> str:
    extracted_sections = []

    try:
        document = fitz.open(path)

        try:
            maximum_pages = min(
                document.page_count,
                5,
            )

            for page_number in range(
                maximum_pages
            ):
                page = document.load_page(
                    page_number
                )

                direct_text = page.get_text(
                    "text"
                ).strip()

                if direct_text:
                    extracted_sections.append(
                        direct_text
                    )

        finally:
            document.close()

    except Exception as error:
        print(
            "PDF extraction failed: "
            f"{type(error).__name__}: "
            f"{error}"
        )
        return ""

    combined_text = "\n".join(
        extracted_sections
    )

    return combined_text[:15000]

router = APIRouter(
    prefix="/ai",
    tags=["AI Security Advisor"],
)


class FileAnalyzeRequest(BaseModel):
    filename: str
    size_kb: float | None = None

class OcrAnalyzeRequest(BaseModel):
    file_id: int
    extracted_text: str

def extract_text_from_file(
    path: str,
) -> str:
    ext = os.path.splitext(
        path
    )[1].lower()

    if ext in [
        ".txt",
        ".csv",
        ".json",
        ".log",
    ]:
        try:
            with open(
                path,
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as file:
                return file.read(15000)

        except Exception as error:
            print(
                "Text extraction failed: "
                f"{type(error).__name__}: "
                f"{error}"
            )
            return ""

    if ext == ".pdf":
        return extract_text_from_pdf(
            path
        )

    return ""

def contains_non_negated_term(
    content: str,
    terms: list[str],
) -> bool:
    for term in terms:
        pattern = rf"\b{re.escape(term)}\b"

        for match in re.finditer(
            pattern,
            content,
        ):
            prefix = content[
                max(0, match.start() - 35):
                match.start()
            ]

            negative_pattern = (
                r"\b(?:no|not|without|does not|doesn't)"
                r"\s+(?:\w+\s+){0,3}$"
            )

            if re.search(
                negative_pattern,
                prefix,
            ):
                continue

            return True

    return False

def predict_risk(
    text: str,
    filename: str,
    size_kb: float,
):
    ext = (
        os.path.splitext(filename)[1]
        .replace(".", "")
        .lower()
    )

    try:
        ext_encoded = encoder.transform(
            [ext]
        )[0]

    except Exception:
        ext_encoded = encoder.transform(
            ["other"]
        )[0]

    content = (
        filename
        + " "
        + text
    ).lower()

    features = {
        "extension_encoded": ext_encoded,
        "size_kb": size_kb,

        "has_password": int(
            "password" in content
        ),

        "has_bank": int(
    contains_non_negated_term(
        content,
        ["bank", "account"],
    )
),

        "has_email": int(
            bool(
                re.search(
                    r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
                    content,
                )
            )
        ),

        "has_phone": int(
            bool(
                re.search(
                    r"\b(?:\+94|0)?7\d{8}\b",
                    content,
                )
            )
        ),

       "has_nic": int(
    bool(
        re.search(
            r"\b(?:nic|national\s+identity(?:\s+card)?|identity\s+card)"
            r"\b[\s:#-]{0,20}"
            r"(?:\d{12}|\d{9}[vVxX])\b",
            content,
            re.IGNORECASE,
        )
    )
),

        "has_card": int(
            bool(
                re.search(
                    r"\b(?:\d[ -]*?){13,16}\b",
                    content,
                )
            )
        ),

        "has_secret": int(
            "secret" in content
        ),

        "has_confidential": int(
    contains_non_negated_term(
        content,
        [
            "confidential",
            "private",
        ],
    )
),

        "has_api_key": int(
            "api key" in content
            or "sk_test" in content
            or "sk_live" in content
        ),

        "has_token": int(
            "token" in content
        ),

        "has_passport": int(
            "passport" in content
        ),

        "has_internal": int(
            "internal" in content
        ),

        "has_project": int(
            "project" in content
        ),

        "has_student": int(
            "student" in content
        ),

        "has_report": int(
            "report" in content
        ),

        "has_invoice": int(
            "invoice" in content
        ),

        "has_salary": int(
            "salary" in content
        ),

        "has_medical": int(
            "medical" in content
            or "patient" in content
            or "prescription" in content
        ),
    }

    data_frame = pd.DataFrame(
        [features]
    )

    risk_model = joblib.load(
        MODEL_PATH
    )

    try:
        probabilities = (
            risk_model.predict_proba(
                data_frame
            )[0]
        )

        model_classes = (
            risk_model.classes_.copy()
        )

    finally:
        del risk_model
        gc.collect()

    prediction_index = (
        probabilities.argmax()
    )

    prediction = model_classes[
        prediction_index
    ]

    confidence = round(
        probabilities[
            prediction_index
        ] * 100,
        2,
    )

    probability_map = {
        class_name: float(probability)
        for class_name, probability in zip(
            model_classes,
            probabilities,
        )
    }
    risk_score = round(
        (
            probability_map.get(
                "Low",
                0,
            ) * 20
            + probability_map.get(
                "Medium",
                0,
            ) * 60
            + probability_map.get(
                "High",
                0,
            ) * 90
        ),
        2,
    )

    findings = []

    labels = {
        "has_password":
            "Password detected",

        "has_bank":
            "Bank/account information detected",

        "has_email":
            "Email address detected",

        "has_phone":
            "Phone number detected",

        "has_nic":
            "NIC-like number detected",

        "has_card":
            "Payment card-like number detected",

        "has_secret":
            "Secret keyword detected",

        "has_confidential":
            "Confidential/private keyword detected",

        "has_api_key":
            "API key pattern detected",

        "has_token":
            "Token pattern detected",

        "has_passport":
            "Passport keyword detected",

        "has_internal":
            "Internal document keyword detected",

        "has_project":
            "Project-related content detected",

        "has_student":
            "Student-related content detected",

        "has_report":
            "Report document detected",

        "has_invoice":
            "Invoice-related content detected",

        "has_salary":
            "Salary information detected",

        "has_medical":
            "Medical/patient information detected",
    }

    for key, label in labels.items():
        if features[key] == 1:
            findings.append(label)

    if not findings:
        findings.append(
            "No sensitive information patterns detected"
        )

    return (
        prediction,
        confidence,
        risk_score,
        findings,
    )


@router.post("/analyze")
def analyze_file(
    data: FileAnalyzeRequest,
):
    filename = data.filename.lower()

    ext = os.path.splitext(
        filename
    )[1]

    score = 10

    findings = [
        "Basic file-name based analysis applied"
    ]

    if ext in [
        ".jpg",
        ".jpeg",
        ".png",
    ]:
        score = 45

        findings.append(
            "Image file may contain personal metadata"
        )

    elif ext in [
        ".pdf",
        ".docx",
        ".xlsx",
        ".txt",
    ]:
        score = 35

        findings.append(
            "Document file may contain private information"
        )

    risk_level = (
        "Medium"
        if score >= 30
        else "Low"
    )

    recommendation = (
        "Biometric Encryption"
        if score >= 30
        else "Standard AES Encryption"
    )

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "findings": findings,
        "reason": findings[0],
    }


@router.get(
    "/analyze-file/{file_id}"
)
def analyze_uploaded_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
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
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    if (
        not file.file_path
        or not os.path.exists(
            file.file_path
        )
    ):
        raise HTTPException(
            status_code=404,
            detail="Uploaded file not found",
        )

    extension = os.path.splitext(
        file.original_filename
    )[1].lower()

    if extension in [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
    ]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Image OCR must be completed on the mobile "
                "device and sent to /ai/analyze-ocr-text."
            ),
        )

    text = extract_text_from_file(
        file.file_path
    )

    if (
        extension == ".pdf"
        and not text.strip()
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "This PDF appears to be scanned or image-based. "
                "OCR text is required for analysis."
            ),
        )

    print(
        f"AI extracted {len(text)} characters "
        f"from {file.original_filename}"
    )

    size_kb = (
        os.path.getsize(
            file.file_path
        )
        / 1024
    )

    (
        risk_level,
        confidence,
        score,
        findings,
    ) = predict_risk(
        text=text,
        filename=file.original_filename,
        size_kb=size_kb,
    )

    if risk_level == "High":
        recommendation = (
            "AES-256 + Biometric Protection"
        )

    elif risk_level == "Medium":
        recommendation = (
            "Biometric Encryption"
        )

    else:
        recommendation = (
            "Standard AES Encryption"
        )

    if (
        findings
        and findings[0]
        != "No sensitive information patterns detected"
    ):
        reason = (
            "Sensitive indicators detected: "
            + ", ".join(
                findings[:4]
            )
        )

    else:
        reason = (
            "The AI model did not detect strong "
            "sensitive-content indicators."
        )

    return {
        "file_id": file.id,
        "filename": file.original_filename,
        "risk_score": score,
        "risk_level": risk_level,
        "confidence": confidence,
        "recommendation": recommendation,
        "findings": findings,
        "reason": reason,
    }
    
@router.post("/analyze-ocr-text")
def analyze_ocr_text(
    data: OcrAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    file = (
    db.query(File)
    .filter(
        File.id == data.file_id,
        File.user_id == current_user.id,
    )
    .first()
)

    if not file:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    if (
        file.file_path
        and os.path.exists(file.file_path)
    ):
        size_kb = (
            os.path.getsize(file.file_path)
            / 1024
        )
    else:
        size_kb = 0.0

    (
        risk_level,
        confidence,
        score,
        findings,
    ) = predict_risk(
        text=data.extracted_text,
        filename=file.original_filename,
        size_kb=size_kb,
    )

    if risk_level == "High":
        recommendation = (
            "AES-256 + Biometric Protection"
        )

    elif risk_level == "Medium":
        recommendation = (
            "Biometric Encryption"
        )

    else:
        recommendation = (
            "Standard AES Encryption"
        )

    if (
        findings
        and findings[0]
        != "No sensitive information patterns detected"
    ):
        reason = (
            "Sensitive indicators detected: "
            + ", ".join(findings[:4])
        )

    else:
        reason = (
            "The AI model did not detect strong "
            "sensitive-content indicators."
        )

    return {
        "file_id": file.id,
        "filename": file.original_filename,
        "risk_score": score,
        "risk_level": risk_level,
        "confidence": confidence,
        "recommendation": recommendation,
        "findings": findings,
        "reason": reason,
    }