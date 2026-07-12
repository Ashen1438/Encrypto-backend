import csv
import random

rows = []

low_templates = [
    "Today I completed my assignment.",
    "Shopping list and simple reminders.",
    "Public announcement content.",
    "Normal personal note without sensitive data.",
]

medium_templates = [
    "Project report with student discussion notes.",
    "Invoice details for business record.",
    "Academic document with internal review comments.",
    "Student project report for university submission.",
    "Internal project discussion and report draft.",
]

high_templates = [
    "Password: Ashen@123 Bank account: 1234567890",
    "API key: sk_test_123456 Secret token: abcdef",
    "Credit card number: 4111 1111 1111 1111",
    "Passport number: N1234567 NIC 200012345678",
    "Confidential salary report and private account details.",
    "Medical patient record with confidential prescription data.",
]

def features(text, ext, size, risk):
    lower = text.lower()

    return [
        ext,
        size,
        int("password" in lower),
        int("bank" in lower or "account" in lower),
        int("@" in lower),
        int("071" in lower or "077" in lower),
        int("nic" in lower),
        int("credit card" in lower or "4111" in lower),
        int("secret" in lower),
        int("confidential" in lower or "private" in lower),
        int("api key" in lower),
        int("token" in lower),
        int("passport" in lower),
        int("internal" in lower),
        int("project" in lower),
        int("student" in lower),
        int("report" in lower),
        int("invoice" in lower),
        int("salary" in lower),
        int("medical" in lower or "patient" in lower or "prescription" in lower),
        risk,
    ]

for _ in range(180):
    text = random.choice(low_templates)
    ext = random.choice(["txt", "jpg", "png"])
    size = random.randint(10, 500)
    rows.append(features(text, ext, size, "Low"))

for _ in range(160):
    text = random.choice(medium_templates)
    ext = random.choice(["txt", "pdf", "docx", "xlsx", "jpg"])
    size = random.randint(300, 5000)
    rows.append(features(text, ext, size, "Medium"))

for _ in range(160):
    text = random.choice(high_templates)
    ext = random.choice(["txt", "csv", "json", "log", "pdf"])
    size = random.randint(50, 10000)
    rows.append(features(text, ext, size, "High"))

random.shuffle(rows)

with open("app/ml/risk_dataset.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "extension",
        "size_kb",
        "has_password",
        "has_bank",
        "has_email",
        "has_phone",
        "has_nic",
        "has_card",
        "has_secret",
        "has_confidential",
        "has_api_key",
        "has_token",
        "has_passport",
        "has_internal",
        "has_project",
        "has_student",
        "has_report",
        "has_invoice",
        "has_salary",
        "has_medical",
        "risk",
    ])
    writer.writerows(rows)

print("Dataset generated: 500 rows with advanced features")