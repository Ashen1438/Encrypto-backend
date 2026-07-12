from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import re
import joblib
import pandas as pd

from app.database import get_db
from app.models.file import File

model = joblib.load("app/ml/risk_model.pkl")
encoder = joblib.load("app/ml/extension_encoder.pkl")

router = APIRouter(prefix="/ai", tags=["AI Security Advisor"])


class FileAnalyzeRequest(BaseModel):
    filename: str
    size_kb: float | None = None


def extract_text_from_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()

    if ext in [".txt", ".csv", ".json", ".log"]:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(5000)
        except Exception:
            return ""

    return ""


def predict_risk(text: str, filename: str, size_kb: float):
    ext = os.path.splitext(filename)[1].replace(".", "").lower()

    try:
        ext_encoded = encoder.transform([ext])[0]
    except Exception:
        ext_encoded = 0

    content = (filename + " " + text).lower()

    features = {
        "extension_encoded": ext_encoded,
        "size_kb": size_kb,
        "has_password": int("password" in content),
        "has_bank": int("bank" in content or "account" in content),
        "has_email": int(bool(re.search(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", content))),
        "has_phone": int(bool(re.search(r"\b(?:\+94|0)?7\d{8}\b", content))),
        "has_nic": int(bool(re.search(r"\b\d{12}\b|\b\d{9}[vVxX]\b", content))),
        "has_card": int(bool(re.search(r"\b(?:\d[ -]*?){13,16}\b", content))),
        "has_secret": int("secret" in content),
        "has_confidential": int("confidential" in content or "private" in content),
        "has_api_key": int("api key" in content or "sk_test" in content or "sk_live" in content),
        "has_token": int("token" in content),
        "has_passport": int("passport" in content),
        "has_internal": int("internal" in content),
        "has_project": int("project" in content),
        "has_student": int("student" in content),
        "has_report": int("report" in content),
        "has_invoice": int("invoice" in content),
        "has_salary": int("salary" in content),
        "has_medical": int("medical" in content or "patient" in content or "prescription" in content),
    }

    df = pd.DataFrame([features])
    prediction = model.predict(df)[0]
    confidence = round(max(model.predict_proba(df)[0]) * 100, 2)

    findings = []

    labels = {
        "has_password": "Password detected",
        "has_bank": "Bank/account information detected",
        "has_email": "Email address detected",
        "has_phone": "Phone number detected",
        "has_nic": "NIC-like number detected",
        "has_card": "Payment card-like number detected",
        "has_secret": "Secret keyword detected",
        "has_confidential": "Confidential/private keyword detected",
        "has_api_key": "API key pattern detected",
        "has_token": "Token pattern detected",
        "has_passport": "Passport keyword detected",
        "has_internal": "Internal document keyword detected",
        "has_project": "Project-related content detected",
        "has_student": "Student-related content detected",
        "has_report": "Report document detected",
        "has_invoice": "Invoice-related content detected",
        "has_salary": "Salary information detected",
        "has_medical": "Medical/patient information detected",
    }

    for key, label in labels.items():
        if features[key] == 1:
            findings.append(label)

    # Hybrid AI rules
    high_flags = [
        "has_password", "has_bank", "has_nic", "has_card",
        "has_api_key", "has_token", "has_passport",
        "has_salary", "has_medical"
    ]

    medium_flags = [
        "has_email", "has_phone", "has_internal",
        "has_project", "has_student", "has_report", "has_invoice"
    ]

    if any(features[k] == 1 for k in high_flags):
        prediction = "High"
        confidence = max(confidence, 95.0)
    elif any(features[k] == 1 for k in medium_flags) and prediction == "Low":
        prediction = "Medium"
        confidence = max(confidence, 85.0)

    if not findings:
        findings.append("No sensitive information patterns detected")

    return prediction, confidence, findings


@router.post("/analyze")
def analyze_file(data: FileAnalyzeRequest):
    filename = data.filename.lower()
    ext = os.path.splitext(filename)[1]

    score = 10
    findings = ["Basic file-name based analysis applied"]

    if ext in [".jpg", ".jpeg", ".png"]:
        score = 45
        findings.append("Image file may contain personal metadata")
    elif ext in [".pdf", ".docx", ".xlsx", ".txt"]:
        score = 35
        findings.append("Document file may contain private information")

    risk_level = "Medium" if score >= 30 else "Low"
    recommendation = "Biometric Encryption" if score >= 30 else "Standard AES Encryption"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "findings": findings,
        "reason": findings[0],
    }


@router.get("/analyze-file/{file_id}")
def analyze_uploaded_file(file_id: int, db: Session = Depends(get_db)):
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if not file.file_path or not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    text = extract_text_from_file(file.file_path)
    size_kb = os.path.getsize(file.file_path) / 1024

    risk_level, confidence, findings = predict_risk(
        text=text,
        filename=file.original_filename,
        size_kb=size_kb,
    )

    if risk_level == "High":
        score = 90
        recommendation = "AES-256 + Biometric Protection"
    elif risk_level == "Medium":
        score = 60
        recommendation = "Biometric Encryption"
    else:
        score = 20
        recommendation = "Standard AES Encryption"

    if findings and findings[0] != "No sensitive information patterns detected":
        reason = "Sensitive indicators detected: " + ", ".join(findings[:4])
    else:
        reason = "The AI model did not detect strong sensitive-content indicators."

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