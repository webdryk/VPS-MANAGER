import logging
import socket
import select
from typing import Optional
from client.protocol_switcher import ProtocolSwitcher
from client.kill_switch import KillSwitch
from client.obfuscation import Obfuscator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TunnelClient:
    def __init__(self, server_ip: str, server_port: int, protocol: str = 'auto'):
        self.server_ip = server_ip
        self.server_port = server_port
        self.protocol = protocol
        self.protocol_switcher = ProtocolSwitcher(server_ip, {})
        self.kill_switch = KillSwitch()
        self.obfuscator = Obfuscator()
        self._running = False
        self._socket = None
        
    def connect(self):
        """Establish connection to VPN server"""
        self.kill_switch.enable()
        
        if self.protocol == 'auto':
            if not self.protocol_switcher.switch_to_best_protocol():
                raise ConnectionError("Could not establish any VPN connection")
        else:
            # Implement protocol-specific connection
            pass
            
        self._running = True
        logger.info("VPN tunnel established")
        
    def disconnect(self):
        """Disconnect from VPN server"""
        self._running = False
        if self._socket:
            self._socket.close()
        self.kill_switch.disable()
        logger.info("VPN tunnel disconnected")
        
    def forward_traffic(self, local_port: int = 1080):
        """Forward local traffic through the tunnel"""
        try:
            local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            local_socket.bind(('127.0.0.1', local_port))
            local_socket.listen(5)
            
            logger.info(f"Forwarding local traffic from port {local_port}")
            
            while self._running:
                readable, _, _ = select.select([local_socket], [], [], 1.0)
                if local_socket in readable:
                    client_socket, addr = local_socket.accept()
                    threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,)
                    ).start()
                    
        except Exception as e:
            logger.error(f"Traffic forwarding error: {e}")
            raise
            
    def _handle_client(self, client_socket: socket.socket):
        """Handle client connection and forward through tunnel"""
        try:
            data = client_socket.recv(4096)
            if data:
                # Obfuscate and forward through tunnel
                obfuscated = self.obfuscator.protocol_mimicry(data)
                self._socket.sendall(obfuscated)
                
                # Receive response and send back to client
                response = self._socket.recv(4096)
                if response:
                    client_socket.sendall(response)
        finally:
            client_socket.close()
            
    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()