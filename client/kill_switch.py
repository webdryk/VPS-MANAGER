import iptc
import time
import threading
import logging
from typing import Optional
from utils.network_utils import get_default_interface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KillSwitch:
    def __init__(self):
        self.active = False
        self.interface = get_default_interface()
        self.monitor_thread: Optional[threading.Thread] = None
        self.vpn_interface = "tun0"
        self._original_rules = []
        
    def _save_original_rules(self):
        """Save current iptables rules for later restoration"""
        table = iptc.Table(iptc.Table.FILTER)
        chain = iptc.Chain(table, "OUTPUT")
        self._original_rules = list(chain.rules)
    
    def enable(self) -> None:
        """Block all non-VPN traffic"""
        if self.active:
            return
            
        self._save_original_rules()
        table = iptc.Table(iptc.Table.FILTER)
        chain = iptc.Chain(table, "OUTPUT")
        
        # Flush existing rules
        chain.flush()
        
        # Accept traffic through VPN interface
        rule = iptc.Rule()
        rule.out_interface = self.vpn_interface
        rule.target = iptc.Target(rule, "ACCEPT")
        chain.insert_rule(rule)
        
        # Accept established connections
        rule = iptc.Rule()
        rule.match = iptc.Match(rule, "conntrack")
        rule.ctstate = "ESTABLISHED,RELATED"
        rule.target = iptc.Target(rule, "ACCEPT")
        chain.insert_rule(rule)
        
        # Reject all other traffic
        rule = iptc.Rule()
        rule.target = iptc.Target(rule, "REJECT")
        chain.insert_rule(rule)
        
        self.active = True
        self.start_monitoring()
        logger.info("Kill switch activated")
    
    def disable(self) -> None:
        """Restore original firewall rules"""
        if not self.active:
            return
            
        self.stop_monitoring()
        
        table = iptc.Table(iptc.Table.FILTER)
        chain = iptc.Chain(table, "OUTPUT")
        chain.flush()
        
        # Restore original rules
        for rule in self._original_rules:
            chain.insert_rule(rule)
        
        self.active = False
        logger.info("Kill switch deactivated")
    
    def start_monitoring(self) -> None:
        """Start monitoring VPN connection in background thread"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
            
        self.monitor_thread = threading.Thread(
            target=self._monitor_connection,
            daemon=True
        )
        self.monitor_thread.start()
        logger.debug("Started kill switch monitor")
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring thread"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            # Thread will stop on next iteration due to self.active flag
            self.monitor_thread.join(timeout=5)
            logger.debug("Stopped kill switch monitor")
    
    def _monitor_connection(self) -> None:
        """Monitor VPN connection and activate emergency block if needed"""
        check_interval = 5  # seconds
        
        while self.active:
            if not self._check_vpn_connection():
                logger.warning("VPN connection lost - activating emergency block")
                self._emergency_block()
                break
            time.sleep(check_interval)
    
    def _check_vpn_connection(self) -> bool:
        """Check if VPN interface is active and has traffic"""
        try:
            # Check if interface exists
            with open(f"/sys/class/net/{self.vpn_interface}/operstate") as f:
                if 'up' not in f.read().lower():
                    return False
            
            # Check for recent traffic (simplified)
            # In production, you'd want more sophisticated checks
            return True
        except Exception as e:
            logger.debug(f"VPN check failed: {e}")
            return False
    
    def _emergency_block(self) -> None:
        """Immediately block all traffic"""
        try:
            table = iptc.Table(iptc.Table.FILTER)
            
            # Block all outgoing traffic
            for chain_name in ["OUTPUT", "FORWARD"]:
                chain = iptc.Chain(table, chain_name)
                chain.flush()
                rule = iptc.Rule()
                rule.target = iptc.Target(rule, "DROP")
                chain.insert_rule(rule)
            
            # Allow local traffic
            chain = iptc.Chain(table, "OUTPUT")
            rule = iptc.Rule()
            rule.out_interface = "lo"
            rule.target = iptc.Target(rule, "ACCEPT")
            chain.insert_rule(rule)
            
            logger.critical("EMERGENCY NETWORK BLOCK ACTIVATED")
        except Exception as e:
            logger.error(f"Failed to activate emergency block: {e}")
    
    def __enter__(self):
        """Context manager support"""
        self.enable()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure cleanup on exit"""
        self.disable()