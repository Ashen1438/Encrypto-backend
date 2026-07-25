import json

import joblib
import pandas as pd

from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


DATASET_PATH = "app/ml/risk_dataset.csv"
MODEL_PATH = "app/ml/risk_model.pkl"
ENCODER_PATH = "app/ml/extension_encoder.pkl"
METRICS_PATH = "app/ml/model_metrics.json"


FEATURES = [
    "extension_encoded",
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
]


# Load dataset
df = pd.read_csv(DATASET_PATH)

print("Dataset rows:", len(df))
print("\nClass distribution:")
print(df["risk"].value_counts())


# Encode file extensions
encoder = LabelEncoder()

df["extension_encoded"] = encoder.fit_transform(
    df["extension"].astype(str)
)


X = df[FEATURES]
y = df["risk"]


# Balanced train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


# Controlled Random Forest
base_model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_split=10,
    min_samples_leaf=4,
    max_features="sqrt",
    class_weight="balanced_subsample",
    random_state=42,
    n_jobs=-1,
)


# Probability calibration
try:
    model = CalibratedClassifierCV(
        estimator=base_model,
        method="sigmoid",
        cv=5,
    )
except TypeError:
    # Compatibility with older scikit-learn versions
    model = CalibratedClassifierCV(
        base_estimator=base_model,
        method="sigmoid",
        cv=5,
    )


print("\nTraining calibrated Random Forest model...")

model.fit(X_train, y_train)


# Test predictions
predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions,
)

balanced_accuracy = balanced_accuracy_score(
    y_test,
    predictions,
)

report = classification_report(
    y_test,
    predictions,
    output_dict=True,
    zero_division=0,
)

matrix = confusion_matrix(
    y_test,
    predictions,
    labels=["Low", "Medium", "High"],
)


# Save trained objects
joblib.dump(
    model,
    MODEL_PATH,
)

joblib.dump(
    encoder,
    ENCODER_PATH,
)


# Save evaluation evidence
metrics = {
    "dataset_rows": int(len(df)),
    "training_rows": int(len(X_train)),
    "testing_rows": int(len(X_test)),
    "class_distribution": {
        key: int(value)
        for key, value in df["risk"]
        .value_counts()
        .to_dict()
        .items()
    },
    "accuracy": float(accuracy),
    "balanced_accuracy": float(
        balanced_accuracy
    ),
    "classification_report": report,
    "confusion_matrix_labels": [
        "Low",
        "Medium",
        "High",
    ],
    "confusion_matrix": matrix.tolist(),
}


with open(
    METRICS_PATH,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        metrics,
        file,
        indent=4,
    )


print("\nModel trained successfully")
print("Accuracy:", round(accuracy, 4))
print(
    "Balanced accuracy:",
    round(balanced_accuracy, 4),
)

print("\nClassification report:")
print(
    classification_report(
        y_test,
        predictions,
        zero_division=0,
    )
)

print("Confusion matrix:")
print(matrix)

print("\nModel saved:", MODEL_PATH)
print("Encoder saved:", ENCODER_PATH)
print("Metrics saved:", METRICS_PATH)