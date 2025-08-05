import logging
import socket
import threading
import time
import select
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
        self._connection_timeout = 1.0  # Timeout for socket operations

    def _handle_connection(self, client_socket: socket.socket, address: tuple):
        """Handle SOCKS5 client connection"""
        try:
            # Set timeout for the client socket
            client_socket.settimeout(5.0)
            
            # Read version identifier/method selection message
            data = client_socket.recv(2)
            if len(data) != 2 or data[0] != 0x05:
                raise ValueError("Invalid SOCKS version or malformed request")

            nmethods = data[1]
            methods = client_socket.recv(nmethods)
            if len(methods) != nmethods:
                raise ValueError("Invalid methods data")

            # Authentication handling
            if self.auth:
                client_socket.sendall(b'\x05\x02')  # Auth required
                
                # Read auth version
                auth_version = client_socket.recv(1)
                if auth_version != b'\x01':
                    raise ValueError("Invalid auth version")

                # Read username and password
                username_len = ord(client_socket.recv(1))
                username = client_socket.recv(username_len).decode('utf-8')
                password_len = ord(client_socket.recv(1))
                password = client_socket.recv(password_len).decode('utf-8')

                if (username, password) != self.auth:
                    client_socket.sendall(b'\x01\x01')  # Auth failed
                    return

                client_socket.sendall(b'\x01\x00')  # Auth success
            else:
                client_socket.sendall(b'\x05\x00')  # No auth required

            # Read client connection request
            request = client_socket.recv(4)
            if len(request) != 4 or request[0] != 0x05:
                raise ValueError("Invalid request format")

            # For simplicity, we'll just respond with success for any request
            # In a real implementation, you would establish the requested connection
            reply = b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00'
            client_socket.sendall(reply)

            # Here you would typically handle the actual proxy connection
            # For this example, we'll just keep the connection open for a while
            while self._running:
                try:
                    # Check if client has disconnected
                    if not client_socket.recv(1, socket.MSG_PEEK):
                        break
                    time.sleep(0.1)
                except (socket.timeout, ConnectionResetError):
                    break

        except Exception as e:
            logger.error(f"SOCKS5 handling error: {e}")
        finally:
            client_socket.close()
            logger.debug(f"Closed connection from {address}")

    def start(self):
        """Start the SOCKS5 server"""
        self._running = True
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind(('0.0.0.0', self.port))
            self._socket.listen(5)
            self._socket.settimeout(self._connection_timeout)

            logger.info(f"SOCKS5 server started on port {self.port}")

            # Main server loop
            while self._running:
                try:
                    # Use select to wait for incoming connections with timeout
                    readable, _, _ = select.select([self._socket], [], [], self._connection_timeout)
                    if self._socket in readable:
                        client_socket, address = self._socket.accept()
                        logger.debug(f"New connection from {address}")
                        
                        handler = threading.Thread(
                            target=self._handle_connection,
                            args=(client_socket, address),
                            daemon=True
                        )
                        handler.start()
                        self._thread_pool.append(handler)
                        
                    # Clean up finished threads
                    self._thread_pool = [t for t in self._thread_pool if t.is_alive()]
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self._running:
                        logger.error(f"Server error: {e}")
                        time.sleep(1)  # Prevent tight loop on errors

        except Exception as e:
            logger.error(f"Failed to start SOCKS5 server: {e}")
            raise

    def stop(self):
        """Stop the server"""
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
        
        # Wait for active connections to finish
        for thread in self._thread_pool:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        logger.info("SOCKS5 server stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()