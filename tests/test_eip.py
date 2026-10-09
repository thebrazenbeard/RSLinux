import socket
import struct
import threading
import unittest
from rslinux5000000.eip import (ENCAPSULATION_HEADER, ProtocolError,
                                decode_list_identity, probe, discover)


def fake_response(name='1769-L32E'):
    device = (struct.pack('<H', 1) +
              struct.pack('!HH4s8s', 2, 44818, socket.inet_aton('192.168.2.10'), b'\0'*8) +
              struct.pack('<HHHBBHI', 1, 14, 123, 20, 13, 0, 0xAABBCCDD) +
              bytes([len(name)]) + name.encode('ascii') + b'\x03')
    cpf = struct.pack('<HHH', 1, 0x000C, len(device)) + device
    return ENCAPSULATION_HEADER.pack(0x63, len(cpf), 0, 0, b'\0'*8, 0), cpf


class DecodeTest(unittest.TestCase):
    def test_identity_fields(self):
        h, p = fake_response()
        i = decode_list_identity(h, p, '192.168.2.10')
        self.assertEqual(i.product_name, '1769-L32E')
        self.assertEqual(i.revision, '20.13')
        self.assertEqual(i.serial_number, 'AABBCCDD')
        self.assertEqual(i.device_address, '192.168.2.10')
        self.assertEqual(i.device_port, 44818)
        self.assertEqual(i.vendor_id, 1)

    def test_rejects_truncation(self):
        h, p = fake_response()
        with self.assertRaises(ProtocolError):
            decode_list_identity(h, p[:-1], '127.0.0.1')

    def test_rejects_wrong_command(self):
        _, p = fake_response()
        h = ENCAPSULATION_HEADER.pack(0x65, len(p), 0, 0, b'\0'*8, 0)
        with self.assertRaises(ProtocolError):
            decode_list_identity(h, p, '127.0.0.1')

    def test_rejects_invalid_name_length(self):
        h, p = fake_response()
        corrupted = bytearray(p)
        # CPF 6 + identity offset 32 => name length
        corrupted[38] = 250
        with self.assertRaises(ProtocolError):
            decode_list_identity(h, bytes(corrupted), '127.0.0.1')

    def test_rejects_unexpected_ip(self):
        with self.assertRaises(ValueError):
            probe('plc.internal.local')

    def test_local_loopback_server(self):
        h, p = fake_response()
        seen = []
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(('127.0.0.1', 0))
            server.listen(1)
            port = server.getsockname()[1]

            def serve():
                conn, _ = server.accept()
                with conn:
                    seen.append(conn.recv(24))
                    conn.sendall(h[:5])
                    conn.sendall(h[5:] + p[:8])
                    conn.sendall(p[8:])

            worker = threading.Thread(target=serve)
            worker.start()
            identity = probe('127.0.0.1', port=port)
            worker.join(timeout=2)
        self.assertEqual(identity.product_name, '1769-L32E')
        self.assertEqual(len(seen), 1)
        self.assertEqual(ENCAPSULATION_HEADER.unpack(seen[0])[0], 0x63)


class DiscoveryTest(unittest.TestCase):
    def test_local_udp_responder(self):
        header, payload = fake_response()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as responder:
            responder.bind(('127.0.0.1', 0))
            port = responder.getsockname()[1]
            def serve():
                data, peer = responder.recvfrom(1024)
                self.assertEqual(ENCAPSULATION_HEADER.unpack(data)[0], 0x63)
                responder.sendto(header + payload, peer)
            worker = threading.Thread(target=serve)
            worker.start()
            devices = discover(broadcast='127.0.0.1', bind='127.0.0.1', port=port, timeout=0.2)
            worker.join(timeout=2)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].queried_address, '127.0.0.1')
        self.assertEqual(devices[0].product_name, '1769-L32E')
