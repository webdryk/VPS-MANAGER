import json
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_wireguard_config(
    private_key: str,
    port: int = 51820,
    peers: list = [],
    interface: str = "wg0",
    address: str = "10.0.0.1/24"
) -> str:
    """Generate WireGuard server configuration"""
    config = f"""[Interface]
PrivateKey = {private_key}
Address = {address}
ListenPort = {port}
"""
    
    for peer in peers:
        config += f"\n[Peer]\nPublicKey = {peer['public_key']}"
        if 'preshared_key' in peer:
            config += f"\nPresharedKey = {peer['preshared_key']}"
        config += f"\nAllowedIPs = {peer['allowed_ips']}\n"
        
    return config

def generate_openvpn_config(
    port: int = 1194,
    protocol: str = 'udp',
    cipher: str = 'AES-256-GCM',
    dh_params: Optional[str] = None,
    ca_cert: Optional[str] = None
) -> str:
    """Generate OpenVPN server configuration"""
    config = f"""port {port}
proto {protocol}
dev tun
topology subnet
server 10.8.0.0 255.255.255.0
cipher {cipher}
keepalive 10 120
persist-key
persist-tun
verb 3
"""
    if dh_params:
        config += f"dh {dh_params}\n"
    if ca_cert:
        config += f"ca {ca_cert}\n"
    return config

def load_config(file_path: str) -> Dict[str, Any]:
    """Load JSON configuration file"""
    try:
        with open(file_path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise

def save_config(config: Dict[str, Any], file_path: str):
    """Save configuration to JSON file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise