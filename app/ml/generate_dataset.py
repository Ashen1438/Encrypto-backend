import csv
import random


random.seed(42)

OUTPUT_PATH = "app/ml/risk_dataset.csv"

TARGET_PER_CLASS = 1000

EXTENSIONS = [
    "txt",
    "pdf",
    "docx",
    "xlsx",
    "csv",
    "json",
    "log",
    "jpg",
    "png",
    "other",
]

FEATURE_NAMES = [
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
]


def chance(probability: float) -> int:
    return int(random.random() < probability)


def weighted_extension(risk: str) -> str:
    if risk == "Low":
        choices = [
            "txt", "txt", "jpg", "jpg",
            "png", "png", "pdf", "docx",
            "xlsx", "other",
        ]

    elif risk == "Medium":
        choices = [
            "pdf", "pdf", "docx", "docx",
            "xlsx", "txt", "jpg", "png",
            "csv", "other",
        ]

    else:
        choices = [
            "pdf", "csv", "json", "log",
            "txt", "docx", "xlsx", "jpg",
            "png", "other",
        ]

    return random.choice(choices)


def generate_low_row() -> list:
    values = {
        "has_password": chance(0.01),
        "has_bank": chance(0.01),
        "has_email": chance(0.08),
        "has_phone": chance(0.05),
        "has_nic": chance(0.005),
        "has_card": chance(0.002),
        "has_secret": chance(0.01),
        "has_confidential": chance(0.02),
        "has_api_key": chance(0.002),
        "has_token": chance(0.005),
        "has_passport": chance(0.002),
        "has_internal": chance(0.05),
        "has_project": chance(0.12),
        "has_student": chance(0.08),
        "has_report": chance(0.10),
        "has_invoice": chance(0.02),
        "has_salary": chance(0.002),
        "has_medical": chance(0.002),
    }

    extension = weighted_extension("Low")
    size_kb = random.randint(5, 1800)

    return [
        extension,
        size_kb,
        *[values[name] for name in FEATURE_NAMES],
        "Low",
    ]


def generate_medium_row() -> list:
    values = {
        "has_password": chance(0.05),
        "has_bank": chance(0.08),
        "has_email": chance(0.35),
        "has_phone": chance(0.25),
        "has_nic": chance(0.04),
        "has_card": chance(0.02),
        "has_secret": chance(0.10),
        "has_confidential": chance(0.18),
        "has_api_key": chance(0.02),
        "has_token": chance(0.04),
        "has_passport": chance(0.02),
        "has_internal": chance(0.38),
        "has_project": chance(0.55),
        "has_student": chance(0.42),
        "has_report": chance(0.58),
        "has_invoice": chance(0.28),
        "has_salary": chance(0.06),
        "has_medical": chance(0.05),
    }

    extension = weighted_extension("Medium")
    size_kb = random.randint(100, 7000)

    return [
        extension,
        size_kb,
        *[values[name] for name in FEATURE_NAMES],
        "Medium",
    ]


def generate_high_row() -> list:
    values = {
        "has_password": chance(0.38),
        "has_bank": chance(0.42),
        "has_email": chance(0.38),
        "has_phone": chance(0.28),
        "has_nic": chance(0.30),
        "has_card": chance(0.22),
        "has_secret": chance(0.36),
        "has_confidential": chance(0.48),
        "has_api_key": chance(0.26),
        "has_token": chance(0.34),
        "has_passport": chance(0.22),
        "has_internal": chance(0.25),
        "has_project": chance(0.18),
        "has_student": chance(0.12),
        "has_report": chance(0.24),
        "has_invoice": chance(0.22),
        "has_salary": chance(0.26),
        "has_medical": chance(0.28),
    }

    strong_features = [
        "has_password",
        "has_bank",
        "has_nic",
        "has_card",
        "has_api_key",
        "has_token",
        "has_passport",
        "has_salary",
        "has_medical",
    ]

    if not any(values[name] for name in strong_features):
        selected_feature = random.choice(strong_features)
        values[selected_feature] = 1

    extension = weighted_extension("High")
    size_kb = random.randint(20, 12000)

    return [
        extension,
        size_kb,
        *[values[name] for name in FEATURE_NAMES],
        "High",
    ]


rows = []
unique_rows = set()

generators = {
    "Low": generate_low_row,
    "Medium": generate_medium_row,
    "High": generate_high_row,
}

for risk, generator in generators.items():
    class_count = 0

    while class_count < TARGET_PER_CLASS:
        row = generator()
        row_key = tuple(row[:-1])

        if row_key in unique_rows:
            continue

        unique_rows.add(row_key)
        rows.append(row)
        class_count += 1


random.shuffle(rows)

with open(
    OUTPUT_PATH,
    "w",
    newline="",
    encoding="utf-8",
) as file:
    writer = csv.writer(file)

    writer.writerow([
        "extension",
        "size_kb",
        *FEATURE_NAMES,
        "risk",
    ])

    writer.writerows(rows)


print(f"Dataset generated: {len(rows)} rows")
print(f"Low rows: {TARGET_PER_CLASS}")
print(f"Medium rows: {TARGET_PER_CLASS}")
print(f"High rows: {TARGET_PER_CLASS}")
print(f"Unique feature rows: {len(unique_rows)}")
print(f"Saved to: {OUTPUT_PATH}")