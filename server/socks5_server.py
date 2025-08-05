import logging
import socket
import threading
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SOCKS5Server:
    def __init__(self, port: int = 1080, auth: Optional[Tuple[str, str]] = None):
        self.port = port
        self.auth = auth
        self._running = False
        self._socket = None
        self._thread_pool = []

    def _handle_connection(self, client_socket: socket.socket, address: tuple):
        """Handle SOCKS5 client connection"""
        try:
            version = client_socket.recv(1)
            if version != b'\x05':
                raise ValueError("Invalid SOCKS version")

            if self.auth:
                client_socket.sendall(b'\x05\x02')  # Auth required
                auth_version = client_socket.recv(1)
                if auth_version != b'\x01':
                    raise ValueError("Invalid auth version")

                username_len = ord(client_socket.recv(1))
                username = client_socket.recv(username_len).decode()
                password_len = ord(client_socket.recv(1))
                password = client_socket.recv(password_len).decode()

                if (username, password) != self.auth:
                    client_socket.sendall(b'\x01\x01')  # Auth failed
                    return

                client_socket.sendall(b'\x01\x00')  # Auth success
            else:
                client_socket.sendall(b'\x05\x00')  # No auth required

            # Fake success (simplified)
            client_socket.sendall(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
        except Exception as e:
            logger.error(f"SOCKS5 handling error: {e}")
        finally:
            client_socket.close()

    def start(self):
        """Start the SOCKS5 server"""
        self._running = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('0.0.0.0', self.port))
        self._socket.listen(5)

        logger.info(f"SOCKS5 server started on port {self.port}")

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
                    target=self._handle_connection,
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
        logger.info("SOCKS5 server stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
