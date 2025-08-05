import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
from server.wireguard_server import WireGuardServer
from server.obfuscation import Obfuscator
from client.protocol_switcher import ProtocolSwitcher, Protocol
from client.kill_switch import KillSwitch
import socket
import iptc

class TestWireGuardServer(unittest.TestCase):
    @patch('subprocess.run')
    @patch('subprocess.getoutput')
    def test_generate_keys(self, mock_getoutput, mock_run):
        mock_getoutput.side_effect = [
            "private_key_123",  # wg genkey
            "public_key_123"    # wg pubkey
        ]
        server = WireGuardServer()
        private, public = server.generate_keys()
        self.assertEqual(private, "private_key_123")
        self.assertEqual(public, "public_key_123")

class TestObfuscator(unittest.TestCase):
    def test_encrypt_decrypt(self):
        o = Obfuscator()
        data = b"test data"
        encrypted = o.encrypt(data)
        self.assertNotEqual(encrypted, data)
        self.assertEqual(o.decrypt(encrypted), data)
    
    def test_xor_roundtrip(self):
        o = Obfuscator()
        data = b"test data"
        obfuscated = o.xor_obfuscate(data)
        self.assertEqual(o.xor_obfuscate(obfuscated), data)

class TestProtocolSwitcher(unittest.TestCase):
    @patch('socket.socket')
    def test_protocol_test(self, mock_socket):
        mock_socket.return_value.recvfrom.return_value = (b'pong', ('8.8.8.8', 53))
        switcher = ProtocolSwitcher("127.0.0.1", {})
        self.assertTrue(switcher.test_connection(Protocol.WIREGUARD))

class TestKillSwitch(unittest.TestCase):
    @patch('iptc.Chain')
    @patch('iptc.Table')
    def test_enable_disable(self, mock_table, mock_chain):
        ks = KillSwitch()
        ks.enable()
        ks.disable()
        self.assertFalse(ks.active)

if __name__ == '__main__':
    unittest.main()