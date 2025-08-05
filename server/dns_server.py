import socket
import requests
import threading
import logging 
from dnslib import DNSRecord, DNSHeader, DNSQuestion, RR, A
from typing import Tuple, Optional
from urllib.parse import quote
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DNSOverHTTPS:
    def __init__(self, 
                 listen_port: int = 53,
                 upstream_dns: str = "https://1.1.1.1/dns-query",
                 timeout: float = 5.0,
                 max_workers: int = 10):
        self.upstream_dns = upstream_dns
        self.listen_port = listen_port
        self.timeout = timeout
        self.max_workers = max_workers
        self._running = False
        self._thread_pool = []
        self._validate_upstream()

    def _validate_upstream(self):
        """Validate the upstream DNS server URL"""
        if not (self.upstream_dns.startswith('https://') and '/dns-query' in self.upstream_dns):
            raise ValueError("Invalid upstream DNS URL - must be HTTPS with /dns-query path")

    def start(self) -> None:
        """Start the DNS server with threaded workers"""
        self._running = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(('0.0.0.0', self.listen_port))
        
        logger.info(f"DNS server started on port {self.listen_port}")
        
        # Create worker threads
        for _ in range(self.max_workers):
            thread = threading.Thread(target=self._worker_loop)
            thread.daemon = True
            thread.start()
            self._thread_pool.append(thread)

    def stop(self) -> None:
        """Stop the DNS server and clean up threads"""
        self._running = False
        if hasattr(self, '_socket'):
            self._socket.close()

        for thread in self._thread_pool:
            thread.join(timeout=1.0)

        logger.info("DNS server stopped")

    def _worker_loop(self) -> None:
        """Worker thread processing DNS queries"""
        while self._running:
            try:
                data, addr = self._socket.recvfrom(1024)
                if data:
                    response = self._handle_query(data)
                    if response:
                        self._socket.sendto(response, addr)
            except socket.error as e:
                if self._running:
                    logger.error(f"Socket error in worker: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in worker: {e}")

    def _handle_query(self, data: bytes) -> Optional[bytes]:
        """Process a DNS query"""
        try:
            request = DNSRecord.parse(data)
            qname = str(request.q.qname)
            
            # Forward to DNS-over-HTTPS with proper headers
            headers = {
                'accept': 'application/dns-message',
                'content-type': 'application/dns-message'
            }
            
            # Use POST instead of GET for better compatibility
            response = requests.post(
                self.upstream_dns,
                headers=headers,
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.content
            else:
                logger.warning(f"Upstream DNS error: {response.status_code}")
                return self._create_error_response()
        except requests.RequestException as e:
            logger.error(f"DNS-over-HTTPS request failed: {e}")
            return self._create_error_response()
        except Exception as e:
            logger.error(f"DNS query processing failed: {e}")
            return self._create_error_response()

    def _create_error_response(self) -> bytes:
        """Create a SERVFAIL DNS response"""
        response = DNSRecord(DNSHeader(id=0, qr=1, rcode=2), q=DNSQuestion("error."))
        return response.pack()

    def __enter__(self):
        """Context manager support"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure cleanup on exit"""
        self.stop()
