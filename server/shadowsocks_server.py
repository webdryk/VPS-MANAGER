import logging
import socket
import threading
from typing import Optional
from cryptography.fernet import Fernet
from utils.encryption import generate_strong_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShadowsocksServer:
    def __init__(self, password: Optional[str] = None, port: int = 8388, method: str = 'aes-256-gcm'):
        self.port = port
        self.method = method
        self.password = password or Fernet.generate_key().decode()
        self._running = False
        self._socket = None
        self._thread_pool = []

    def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using the chosen method"""
        if self.method.startswith('aes-256'):
            cipher = Fernet(generate_strong_key(self.password))
            return cipher.encrypt(data)
        return data

    def _decrypt_data(self, data: bytes) -> bytes:
        """Decrypt data using the chosen method"""
        if self.method.startswith('aes-256'):
            cipher = Fernet(generate_strong_key(self.password))
            return cipher.decrypt(data)
        return data

    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle a client connection"""
        try:
            while self._running:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                decrypted = self._decrypt_data(data)
                response = b"ACK: " + decrypted
                encrypted_response = self._encrypt_data(response)
                client_socket.send(encrypted_response)
        except Exception as e:
            logger.error(f"Client handling error: {e}")
        finally:
            client_socket.close()

    def start(self):
        """Start the Shadowsocks server"""
        self._running = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('0.0.0.0', self.port))
        self._socket.listen(5)

        logger.info(f"Shadowsocks server started on port {self.port} (method: {self.method})")

        # Start acceptor thread
        acceptor = threading.Thread(target=self._accept_connections)
        acceptor.daemon = True
        acceptor.start()
        self._thread_pool.append(acceptor)

    def _accept_connections(self):
        """Accept incoming connections"""
        while self._running:
            try:
                client_socket, address = self._socket.accept()
                handler = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address)
                )
                handler.daemon = True
                handler.start()
                self._thread_pool.append(handler)
            except socket.error:
                if self._running:
                    logger.error("Socket accept error")

    def stop(self):
        """Stop the server"""
        self._running = False
        if self._socket:
            self._socket.close()
        for thread in self._thread_pool:
            thread.join(timeout=1.0)
        logger.info("Shadowsocks server stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
