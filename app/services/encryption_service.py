from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import base64
import os


PASSWORD_MAGIC = b"ENCRYPTO_PASSWORD_V2"
SALT_SIZE = 16
MODE_SIZE = 16
PBKDF2_ITERATIONS = 600_000

VALID_PASSWORD_MODES = {
    "hybrid",
    "password_only",
}


def generate_key() -> bytes:
    return Fernet.generate_key()


def encrypt_file(
    input_path: str,
    output_path: str,
    key: bytes,
) -> None:
    fernet = Fernet(key)

    with open(input_path, "rb") as source_file:
        data = source_file.read()

    encrypted_data = fernet.encrypt(data)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as output_file:
        output_file.write(encrypted_data)


def decrypt_file(
    input_path: str,
    output_path: str,
    key: bytes,
) -> None:
    fernet = Fernet(key)

    with open(input_path, "rb") as source_file:
        encrypted_data = source_file.read()

    decrypted_data = fernet.decrypt(encrypted_data)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as output_file:
        output_file.write(decrypted_data)


def derive_key_from_password(
    password: str,
    salt: bytes,
) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )

    derived_key = kdf.derive(password.encode("utf-8"))

    return base64.urlsafe_b64encode(derived_key)


def encrypt_file_with_password(
    input_path: str,
    output_path: str,
    password: str,
    mode: str,
) -> None:
    if mode not in VALID_PASSWORD_MODES:
        raise ValueError("Invalid protection mode")

    salt = os.urandom(SALT_SIZE)

    key = derive_key_from_password(
        password=password,
        salt=salt,
    )

    fernet = Fernet(key)

    with open(input_path, "rb") as source_file:
        original_data = source_file.read()

    encrypted_data = fernet.encrypt(original_data)

    mode_bytes = mode.encode("utf-8")

    if len(mode_bytes) > MODE_SIZE:
        raise ValueError("Protection mode is too long")

    padded_mode = mode_bytes.ljust(MODE_SIZE, b"\0")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as output_file:
        output_file.write(PASSWORD_MAGIC)
        output_file.write(padded_mode)
        output_file.write(salt)
        output_file.write(encrypted_data)

def get_password_file_mode(input_path: str) -> str:
    with open(input_path, "rb") as source_file:
        magic = source_file.read(len(PASSWORD_MAGIC))

        if magic != PASSWORD_MAGIC:
            raise ValueError(
                "This file is not a supported Encrypto password file"
            )

        mode_bytes = source_file.read(MODE_SIZE)

    mode = mode_bytes.rstrip(b"\0").decode("utf-8")

    if mode not in VALID_PASSWORD_MODES:
        raise ValueError(
            "Invalid or unsupported protection mode in file"
        )

    return mode

def decrypt_file_with_password(
    input_path: str,
    output_path: str,
    password: str,
    expected_mode: str,
) -> None:
    if expected_mode not in VALID_PASSWORD_MODES:
        raise ValueError("Invalid requested protection mode")

    with open(input_path, "rb") as source_file:
        encrypted_file_data = source_file.read()

    magic_end = len(PASSWORD_MAGIC)

    minimum_size = (
        magic_end
        + MODE_SIZE
        + SALT_SIZE
        + 1
    )

    if len(encrypted_file_data) < minimum_size:
        raise ValueError("Invalid password-encrypted file")

    magic = encrypted_file_data[:magic_end]

    if magic != PASSWORD_MAGIC:
        raise ValueError(
            "This file is not a supported Encrypto password file"
        )

    mode_start = magic_end
    mode_end = mode_start + MODE_SIZE

    stored_mode = (
        encrypted_file_data[mode_start:mode_end]
        .rstrip(b"\0")
        .decode("utf-8")
    )

    if stored_mode not in VALID_PASSWORD_MODES:
        raise ValueError(
            "Invalid or unsupported protection mode in file"
        )

    if stored_mode != expected_mode:
        readable_mode = stored_mode.replace("_", " ").title()

        raise ValueError(
            f"Protection mode mismatch. "
            f"This file requires {readable_mode} mode."
        )

    salt_start = mode_end
    salt_end = salt_start + SALT_SIZE

    salt = encrypted_file_data[salt_start:salt_end]
    encrypted_data = encrypted_file_data[salt_end:]

    key = derive_key_from_password(
        password=password,
        salt=salt,
    )

    fernet = Fernet(key)

    try:
        decrypted_data = fernet.decrypt(encrypted_data)
    except InvalidToken as error:
        raise ValueError(
            "Invalid password or corrupted encrypted file"
        ) from error

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as output_file:
        output_file.write(decrypted_data)