from cryptography.fernet import Fernet, InvalidToken
import socket
import struct
import logging
from typing import Optional, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Obfuscator:
    def __init__(self, key: Optional[bytes] = None):
        """Initialize with optional key (otherwise generates new)"""
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)

    def xor_obfuscate(self, data: bytes, key: bytes = b'\xAA\x55\xAA\x55') -> bytes:
        """Lightweight XOR obfuscation (not for security, only obfuscation)"""
        if not data:
            raise ValueError("No data to obfuscate")
        logger.debug(f"Obfuscating {len(data)} bytes of data with XOR")
        return bytes(x ^ key[i % len(key)] for i, x in enumerate(data))

    def tls_wrap(self, data: bytes) -> bytes:
        """Wrap data with fake TLS header"""
        if len(data) > 65535:
            raise ValueError("Data too large for TLS wrapping")
        logger.debug(f"Wrapping data with fake TLS header: {len(data)} bytes")
        return b'\x17\x03\x03' + struct.pack('>H', len(data)) + data

    def protocol_mimicry(self, data: bytes, protocol: str = 'https') -> bytes:
        """Make traffic look like specified protocol"""
        if protocol == 'https':
            return self.tls_wrap(data)
        elif protocol == 'dns':
            return self._make_like_dns(data)
        else:
            return data

    def _make_like_dns(self, data: bytes) -> bytes:
        """Make data look like DNS traffic"""
        dns_header = b'\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
        max_payload = 512 - len(dns_header) - 5
        payload = data[:max_payload]
        return dns_header + payload

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data with Fernet (AES-128-CBC)"""
        try:
            logger.debug("Encrypting data using Fernet encryption")
            return self.cipher.encrypt(data)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt Fernet-encrypted data"""
        try:
            logger.debug("Decrypting data using Fernet decryption")
            return self.cipher.decrypt(data)
        except InvalidToken as e:
            logger.error(f"Decryption failed - invalid token: {e}")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def get_key(self) -> bytes:
        """Get the encryption key (for sharing with authorized peers)"""
        return self.key
