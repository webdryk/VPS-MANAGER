"""
VPN Tunnel Package - Comprehensive VPN solution with multiple protocols and obfuscation

Features:
- WireGuard, OpenVPN, Shadowsocks, and SOCKS5 support
- Traffic obfuscation (XOR, TLS, DNS mimicry)
- Protocol auto-switching and fallback
- Kill switch functionality
- DNS-over-HTTPS support
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import key components for easier access
from .server import WireGuardServer, OpenVPNServer, ShadowsocksServer, SOCKS5Server
from .client import TunnelClient, ProtocolSwitcher, KillSwitch

# Package-level initialization
def initialize(log_level="INFO"):
    """Initialize package with specified log level"""
    import logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Export symbols
__all__ = [
    'WireGuardServer',
    'OpenVPNServer',
    'ShadowsocksServer',
    'SOCKS5Server',
    'TunnelClient',
    'ProtocolSwitcher',
    'KillSwitch',
    'initialize'
]