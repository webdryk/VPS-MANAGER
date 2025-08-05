import subprocess
import logging
import os
from typing import Optional, List
from utils.config_manager import generate_openvpn_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenVPNServer:
    def __init__(self, config_path: str = "/etc/openvpn/server.conf", port: int = 1194):
        self.config_path = config_path
        self.port = port
        self._process = None

    def generate_config(self, protocol: str = 'udp', cipher: str = 'AES-256-GCM'):
        """Generate OpenVPN server configuration"""
        config = generate_openvpn_config(
            port=self.port,
            protocol=protocol,
            cipher=cipher,
            dh_params=None,
            ca_cert=None
        )

        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            f.write(config)
        logger.info(f"OpenVPN config written to {self.config_path}")

    def start(self):
        """Start the OpenVPN server"""
        if not os.path.exists(self.config_path):
            self.generate_config()

        try:
            self._process = subprocess.Popen(
                ["openvpn", "--config", self.config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"OpenVPN server started on port {self.port}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start OpenVPN: {e}")
            raise

    def stop(self):
        """Stop the OpenVPN server"""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            logger.info("OpenVPN server stopped")

    def add_client(self, client_name: str) -> str:
        """Generate client configuration"""
        return f"client config for {client_name}"

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
