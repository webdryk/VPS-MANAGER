import socket
import logging
import subprocess
from typing import Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_default_interface() -> str:
    """Get the system's default network interface"""
    try:
        route = subprocess.check_output("ip route | grep default", shell=True).decode()
        return route.split()[4]
    except Exception as e:
        logger.warning(f"Could not determine default interface: {e}")
        return "eth0"

def validate_port(port: int):
    """Validate that a port number is valid"""
    if not 1 <= port <= 65535:
        raise ValueError(f"Invalid port number: {port}")

def validate_ip(ip: str):
    """Validate an IP address"""
    try:
        socket.inet_aton(ip)
    except socket.error:
        raise ValueError(f"Invalid IP address: {ip}")

def get_public_ip() -> Optional[str]:
    """Get the public IP address of the server"""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as e:
        logger.warning(f"Could not determine public IP: {e}")
        return None

def is_port_open(host: str, port: int) -> bool:
    """Check if a network port is open"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False