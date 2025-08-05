from cryptography.fernet import Fernet, InvalidToken
import socket
import struct
import logging
from typing import Optional, Union
from utils.encryption import generate_strong_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClientObfuscator:
    def __init__(self, key: Optional[bytes] = None, obfuscation_mode: str = 'tls'):
        """
        Initialize client-side obfuscator
        
        Args:
            key: Pre-shared key for encryption (None generates new)
            obfuscation_mode: Default obfuscation method ('xor', 'tls', 'dns', or 'none')
        """
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.obfuscation_mode = obfuscation_mode
        self.sequence_counter = 0  # For sequence-based obfuscation
        
    def set_mode(self, mode: str):
        """Set the obfuscation mode (xor/tls/dns/none)"""
        valid_modes = ['xor', 'tls', 'dns', 'none']
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of {valid_modes}")
        self.obfuscation_mode = mode
        
    def obfuscate(self, data: bytes, mode: Optional[str] = None) -> bytes:
        """
        Obfuscate outgoing data with the specified method
        
        Args:
            data: Original data to obfuscate
            mode: Override the instance's default mode
            
        Returns:
            Obfuscated data ready for transmission
        """
        mode = mode or self.obfuscation_mode
        
        if mode == 'none':
            return data
        elif mode == 'xor':
            return self._xor_obfuscate(data)
        elif mode == 'tls':
            return self._tls_wrap(data)
        elif mode == 'dns':
            return self._dns_mimic(data)
        else:
            raise ValueError(f"Unknown obfuscation mode: {mode}")

    def deobfuscate(self, data: bytes, mode: Optional[str] = None) -> bytes:
        """
        Deobfuscate incoming data
        
        Args:
            data: Obfuscated data received
            mode: Override the instance's default mode
            
        Returns:
            Original data after deobfuscation
        """
        mode = mode or self.obfuscation_mode
        
        if mode == 'none':
            return data
        elif mode == 'xor':
            return self._xor_deobfuscate(data)
        elif mode == 'tls':
            return self._tls_unwrap(data)
        elif mode == 'dns':
            return self._dns_demimic(data)
        else:
            raise ValueError(f"Unknown obfuscation mode: {mode}")

    def _xor_obfuscate(self, data: bytes, key: bytes = b'\xAA\x55\xAA\x55') -> bytes:
        """Lightweight XOR obfuscation (not for security, only obfuscation)"""
        if not data:
            raise ValueError("No data to obfuscate")
        
        # Include sequence counter to make patterns less obvious
        seq_bytes = self.sequence_counter.to_bytes(4, 'big')
        self.sequence_counter = (self.sequence_counter + 1) % 65536
        
        # XOR with rotating key + sequence
        extended_key = key + seq_bytes
        return bytes(x ^ extended_key[i % len(extended_key)] for i, x in enumerate(data))

    def _xor_deobfuscate(self, data: bytes) -> bytes:
        """Reverse XOR obfuscation"""
        return self._xor_obfuscate(data)  # XOR is symmetric

    def _tls_wrap(self, data: bytes) -> bytes:
        """Wrap data with fake TLS header"""
        if len(data) > 65535:
            raise ValueError("Data too large for TLS wrapping")
        
        # Simulate TLS 1.3 application data
        header = b'\x17\x03\x03' + struct.pack('>H', len(data))
        
        # Add some random padding to vary packet sizes
        padding_len = self.sequence_counter % 32
        padding = bytes([padding_len] * padding_len) if padding_len > 0 else b''
        self.sequence_counter = (self.sequence_counter + 1) % 65536
        
        return header + data + padding

    def _tls_unwrap(self, data: bytes) -> bytes:
        """Extract data from TLS-like wrapper"""
        if len(data) < 5:
            raise ValueError("Invalid TLS wrapper - too short")
            
        # Skip header (3 bytes) and length (2 bytes)
        payload_length = struct.unpack('>H', data[3:5])[0]
        
        if len(data) < 5 + payload_length:
            raise ValueError("Invalid TLS wrapper - payload truncated")
            
        return data[5:5+payload_length]

    def _dns_mimic(self, data: bytes) -> bytes:
        """Make data look like DNS traffic"""
        # DNS header (transaction ID + flags + 1 question)
        header = b'\x00\x00'  # Transaction ID
        header += b'\x01\x00'  # Flags (standard query)
        header += b'\x00\x01'  # 1 question
        header += b'\x00\x00'  # 0 answer RRs
        header += b'\x00\x00'  # 0 authority RRs
        header += b'\x00\x00'  # 0 additional RRs
        
        # Question section (for a fake A record query)
        question = b'\x07example\x03com\x00'  # example.com
        question += b'\x00\x01'  # Type A
        question += b'\x00\x01'  # Class IN
        
        # Payload (our actual data)
        max_payload = 512 - len(header) - len(question) - 2  # 2 bytes for length
        payload = data[:max_payload]
        
        # Build final packet
        return header + question + struct.pack('>H', len(payload)) + payload

    def _dns_demimic(self, data: bytes) -> bytes:
        """Extract data from DNS-like packet"""
        # Skip DNS header (12 bytes) and question section (variable)
        try:
            # Find end of question name (null byte)
            null_pos = data[12:].find(b'\x00')
            if null_pos == -1:
                raise ValueError("Invalid DNS mimic - no null terminator")
                
            # Question ends after null byte + 4 bytes (type and class)
            question_end = 12 + null_pos + 5
            
            if len(data) < question_end + 2:
                raise ValueError("Invalid DNS mimic - truncated")
                
            # Get payload length (2 bytes after question)
            payload_len = struct.unpack('>H', data[question_end:question_end+2])[0]
            
            if len(data) < question_end + 2 + payload_len:
                raise ValueError("Invalid DNS mimic - payload truncated")
                
            return data[question_end+2:question_end+2+payload_len]
        except Exception as e:
            logger.error(f"DNS demimic failed: {e}")
            raise

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data with Fernet (AES-128-CBC)"""
        try:
            return self.cipher.encrypt(data)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt Fernet-encrypted data"""
        try:
            return self.cipher.decrypt(data)
        except InvalidToken as e:
            logger.error(f"Decryption failed - invalid token: {e}")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def get_key(self) -> bytes:
        """Get the encryption key (for sharing with server)"""
        return self.key

    def rotate_key(self):
        """Generate a new encryption key"""
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        logger.info("Encryption key rotated")