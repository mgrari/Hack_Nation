from cryptography.fernet import Fernet

from config import settings

_fernet = Fernet(settings.fernet_key.encode())


def encrypt_bytes(data: bytes) -> bytes:
    return _fernet.encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    return _fernet.decrypt(token)
