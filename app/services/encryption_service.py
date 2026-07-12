from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import base64
import os


PASSWORD_MAGIC = b"ENCRYPTO_PASSWORD_V1"
SALT_SIZE = 16
PBKDF2_ITERATIONS = 600_000


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
) -> None:
    salt = os.urandom(SALT_SIZE)

    key = derive_key_from_password(
        password=password,
        salt=salt,
    )

    fernet = Fernet(key)

    with open(input_path, "rb") as source_file:
        original_data = source_file.read()

    encrypted_data = fernet.encrypt(original_data)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as output_file:
        output_file.write(PASSWORD_MAGIC)
        output_file.write(salt)
        output_file.write(encrypted_data)


def decrypt_file_with_password(
    input_path: str,
    output_path: str,
    password: str,
) -> None:
    with open(input_path, "rb") as source_file:
        encrypted_file_data = source_file.read()

    header_size = len(PASSWORD_MAGIC)

    if len(encrypted_file_data) <= header_size + SALT_SIZE:
        raise ValueError("Invalid password-encrypted file")

    magic = encrypted_file_data[:header_size]

    if magic != PASSWORD_MAGIC:
        raise ValueError("This file is not password encrypted")

    salt_start = header_size
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