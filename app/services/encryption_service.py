from cryptography.fernet import Fernet
import os

# generate key (later AI logic add karamu)
def generate_key():
    return Fernet.generate_key()

def encrypt_file(input_path: str, output_path: str, key: bytes):
    fernet = Fernet(key)

    with open(input_path, "rb") as file:
        data = file.read()

    encrypted_data = fernet.encrypt(data)

    with open(output_path, "wb") as file:
        file.write(encrypted_data)

def decrypt_file(input_path: str, output_path: str, key: bytes):
    fernet = Fernet(key)

    with open(input_path, "rb") as file:
        encrypted_data = file.read()

    decrypted_data = fernet.decrypt(encrypted_data)

    with open(output_path, "wb") as file:
        file.write(decrypted_data)