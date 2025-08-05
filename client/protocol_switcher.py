import socket
import time
import logging
from enum import Enum, auto
from typing import Dict, Optional
from dataclasses import dataclass
import backoff

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Protocol(Enum):
    WIREGUARD = auto()
    SHADOWSOCKS = auto()
    OPENVPN = auto()
    SOCKS5 = auto()

@dataclass
class ProtocolConfig:
    port: int
    timeout: float = 2.0
    retries: int = 3

class ProtocolSwitcher:
    PROTOCOL_CONFIGS: Dict[Protocol, ProtocolConfig] = {
        Protocol.WIREGUARD: ProtocolConfig(port=51820, timeout=1.5),
        Protocol.SHADOWSOCKS: ProtocolConfig(port=8388, timeout=2.0),
        Protocol.OPENVPN: ProtocolConfig(port=1194, timeout=2.5, retries=2),
        Protocol.SOCKS5: ProtocolConfig(port=1080, timeout=3.0)
    }
    
    def __init__(self, server_ip: str, config: Dict):
        self.server_ip = server_ip
        self.config = config
        self.current_protocol: Optional[Protocol] = None
        self.protocol_priority = list(Protocol)
    
    @backoff.on_exception(backoff.expo, 
                         socket.error, 
                         max_tries=3)
    def test_connection(self, protocol: Protocol) -> bool:
        """Test if protocol is available with retries and backoff"""
        config = self.PROTOCOL_CONFIGS[protocol]
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(config.timeout)
                s.sendto(b'ping', (self.server_ip, config.port))
                data, _ = s.recvfrom(1024)
                return data == b'pong'
        except socket.timeout:
            logger.debug(f"Timeout testing {protocol.name}")
            return False
        except socket.error as e:
            logger.warning(f"Socket error testing {protocol.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error testing {protocol.name}: {e}")
            return False
    
    def switch_to_best_protocol(self) -> bool:
        """Find and activate the best available protocol"""
        for protocol in self.protocol_priority:
            try:
                if self.test_connection(protocol):
                    if self._activate_protocol(protocol):
                        self.current_protocol = protocol
                        logger.info(f"Switched to {protocol.name}")
                        return True
            except Exception as e:
                logger.error(f"Failed to test {protocol.name}: {e}")
                continue
        
        logger.error("No working protocols available")
        return False
    
    def _activate_protocol(self, protocol: Protocol) -> bool:
        """Activate the specified protocol"""
        try:
            if protocol == Protocol.WIREGUARD:
                return self._activate_wireguard()
            elif protocol == Protocol.SHADOWSOCKS:
                return self._activate_shadowsocks()
            elif protocol == Protocol.OPENVPN:
                return self._activate_openvpn()
            elif protocol == Protocol.SOCKS5:
                return self._activate_socks5()
            else:
                raise ValueError(f"Unknown protocol: {protocol}")
        except Exception as e:
            logger.error(f"Failed to activate {protocol.name}: {e}")
            return False
    
    def _activate_wireguard(self) -> bool:
        """Implement WireGuard activation"""
        # Implementation would use wg-quick or similar
        return True
    
    def _activate_shadowsocks(self) -> bool:
        """Implement Shadowsocks activation"""
        # Implementation would start shadowsocks client
        return True
    
    def _activate_openvpn(self) -> bool:
        """Implement OpenVPN activation"""
        # Implementation would start OpenVPN client
        return True
    
    def _activate_socks5(self) -> bool:
        """Implement SOCKS5 activation"""
        # Implementation would configure system proxy
        return True