import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

DATASET_PATH = "app/ml/risk_dataset.csv"
MODEL_PATH = "app/ml/risk_model.pkl"
ENCODER_PATH = "app/ml/extension_encoder.pkl"

df = pd.read_csv(DATASET_PATH)

encoder = LabelEncoder()
df["extension_encoded"] = encoder.fit_transform(df["extension"])

features = [
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

X = df[features]
y = df["risk"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

joblib.dump(model, MODEL_PATH)
joblib.dump(encoder, ENCODER_PATH)

print("Model trained successfully")
print("Accuracy:", accuracy)
print("Model saved:", MODEL_PATH)