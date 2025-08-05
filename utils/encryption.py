import os
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_strong_key(password: str, salt: Optional[bytes] = None) -> bytes:
    """Generate a strong encryption key from a password"""
    try:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        
        salt = salt or os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())
    except Exception as e:
        logger.error(f"Key generation failed: {e}")
        raise

class AES256Cipher:
    def __init__(self, key: bytes):
        """Initialize with a 32-byte key"""
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
        self.key = key
        
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data with AES-256-CBC"""
        try:
            iv = os.urandom(16)
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data) + padder.finalize()
            
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            encrypted = encryptor.update(padded_data) + encryptor.finalize()
            return iv + encrypted
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
            
    def decrypt(self, data: bytes) -> bytes:
        """Decrypt AES-256-CBC encrypted data"""
        try:
            iv = data[:16]
            encrypted = data[16:]
            
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            padded = decryptor.update(encrypted) + decryptor.finalize()
            
            unpadder = padding.PKCS7(128).unpadder()
            return unpadder.update(padded) + unpadder.finalize()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise