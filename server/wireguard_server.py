import os
import subprocess
import logging
from typing import List, Tuple
from utils.config_manager import generate_wireguard_config
from utils.network_utils import validate_port, validate_ip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WireGuardServer:
    def __init__(self, config_path="/etc/wireguard/wg0.conf"):
        self.config_path = config_path
        self.interface = "wg0"
        self._validate_requirements()

    def _validate_requirements(self):
        """Check if WireGuard tools are installed and config path is writable"""
        try:
            subprocess.run(["wg", "--version"], check=True, 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not os.access(os.path.dirname(self.config_path), os.W_OK):
                raise PermissionError(f"Cannot write to {self.config_path}")
        except (subprocess.CalledProcessError, PermissionError) as e:
            logger.error(f"WireGuard requirement check failed: {e}")
            raise

    def generate_keys(self) -> Tuple[str, str]:
        """Securely generate WireGuard key pair"""
        try:
            private_key = subprocess.getoutput("wg genkey")
            public_key = subprocess.getoutput(f"echo '{private_key}' | wg pubkey")
            if not (private_key and public_key):
                raise ValueError("Key generation failed")
            return private_key, public_key
        except Exception as e:
            logger.error(f"Key generation error: {e}")
            raise

    def setup_server(self, port: int = 51820) -> None:
        """Configure and start WireGuard server"""
        validate_port(port)
        
        try:
            if not os.path.exists(self.config_path):
                private_key, public_key = self.generate_keys()
                config = generate_wireguard_config(
                    private_key=private_key,
                    port=port,
                    peers=[]
                )
                with open(self.config_path, 'w') as f:
                    f.write(config)
                logger.info(f"WireGuard config created at {self.config_path}")
            
            self.start()
            logger.info(f"WireGuard server started on port {port}")
        except Exception as e:
            logger.error(f"Server setup failed: {e}")
            raise

    def add_peer(self, peer_public_key: str, allowed_ips: List[str]) -> str:
        """Add a new peer to the WireGuard configuration"""
        if not peer_public_key or not allowed_ips:
            raise ValueError("Invalid peer configuration")
        
        for ip in allowed_ips:
            validate_ip(ip)
        
        try:
            # Generate peer preshared key
            preshared_key = subprocess.getoutput("wg genpsk")
            
            # Append peer to config file
            peer_config = f"\n[Peer]\nPublicKey = {peer_public_key}"
            peer_config += f"\nPresharedKey = {preshared_key}"
            peer_config += f"\nAllowedIPs = {', '.join(allowed_ips)}\n"
            
            with open(self.config_path, 'a') as f:
                f.write(peer_config)
            
            # Reload configuration
            subprocess.run(["wg", "syncconf", self.interface, self.config_path], check=True)
            
            logger.info(f"Added peer with public key: {peer_public_key}")
            return preshared_key
        except Exception as e:
            logger.error(f"Failed to add peer: {e}")
            raise

    def start(self) -> None:
        """Start WireGuard interface"""
        try:
            subprocess.run(["wg-quick", "up", self.interface], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start WireGuard: {e}")
            raise

    def stop(self) -> None:
        """Stop WireGuard interface"""
        try:
            subprocess.run(["wg-quick", "down", self.interface], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop WireGuard: {e}")
            raise

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure cleanup on exit"""
        self.stop()
