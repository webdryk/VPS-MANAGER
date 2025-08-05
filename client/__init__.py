"""
VPN Client Components

Available modules:
- tunnel_client: Main VPN tunnel client
- protocol_switcher: Protocol selection and fallback
- kill_switch: Network kill switch
- traffic_monitor: Bandwidth monitoring
- obfuscation: Client-side traffic obfuscation
"""

from .tunnel_client import TunnelClient
from .protocol_switcher import ProtocolSwitcher, Protocol
from .kill_switch import KillSwitch
from .traffic_monitor import TrafficMonitor
from .obfuscation import ClientObfuscator

__all__ = [
    'TunnelClient',
    'ProtocolSwitcher',
    'Protocol',
    'KillSwitch',
    'TrafficMonitor',
    'ClientObfuscator'
]