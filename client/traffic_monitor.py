import time
import threading
import logging
import psutil
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrafficMonitor:
    def __init__(self, interval: float = 5.0):
        self.interval = interval
        self._running = False
        self._thread = None
        self.stats = {
            'bytes_sent': 0,
            'bytes_recv': 0,
            'start_time': time.time()
        }
        
    def start(self):
        """Start monitoring network traffic"""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop)
        self._thread.daemon = True
        self._thread.start()
        logger.info("Traffic monitor started")
        
    def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Traffic monitor stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        last_sent = 0
        last_recv = 0
        
        while self._running:
            net_io = psutil.net_io_counters()
            current_sent = net_io.bytes_sent
            current_recv = net_io.bytes_recv
            
            self.stats['bytes_sent'] = current_sent
            self.stats['bytes_recv'] = current_recv
            self.stats['upload_speed'] = (current_sent - last_sent) / self.interval
            self.stats['download_speed'] = (current_recv - last_recv) / self.interval
            
            last_sent = current_sent
            last_recv = current_recv
            time.sleep(self.interval)
            
    def get_stats(self) -> Dict:
        """Get current traffic statistics"""
        uptime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'uptime': uptime,
            'avg_upload': self.stats['bytes_sent'] / uptime if uptime > 0 else 0,
            'avg_download': self.stats['bytes_recv'] / uptime if uptime > 0 else 0
        }
        
    def __enter__(self):
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()