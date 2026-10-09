"""Minimal, read-only EtherNet/IP ListIdentity exchange (encapsulation command 0x63).

No CIP sessions, tag reads/writes, firmware operations or configuration writes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import ipaddress
import socket
import struct
import time

EIP_PORT = 44818
LIST_IDENTITY = 0x0063
ENCAPSULATION_HEADER = struct.Struct('<HHII8sI')
MAX_REPLY_LENGTH = 4096


class ProtocolError(ValueError):
    """Malformed or unexpected EtherNet/IP response."""


@dataclass(frozen=True)
class Identity:
    queried_address: str
    device_address: str
    device_port: int
    vendor_id: int
    device_type: int
    product_code: int
    revision: str
    status: int
    serial_number: str
    product_name: str
    state: int

    def as_dict(self) -> dict:
        return asdict(self)


def _receive_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        part = sock.recv(remaining)
        if not part:
            raise ProtocolError('Connection closed before complete response')
        chunks.append(part)
        remaining -= len(part)
    return b''.join(chunks)


def decode_list_identity(header: bytes, data: bytes, queried_address: str) -> Identity:
    if len(header) != ENCAPSULATION_HEADER.size:
        raise ProtocolError('Invalid encapsulation header length')
    command, length, _session, status, _context, options = ENCAPSULATION_HEADER.unpack(header)
    if command != LIST_IDENTITY:
        raise ProtocolError(f'Unexpected encapsulation command: 0x{command:04x}')
    if length != len(data) or length > MAX_REPLY_LENGTH:
        raise ProtocolError('Encapsulation payload length mismatch or too large')
    if status:
        raise ProtocolError(f'Encapsulation error: 0x{status:08x}')
    if options:
        raise ProtocolError('Nonzero encapsulation options')
    if len(data) < 2:
        raise ProtocolError('Missing Common Packet Format item count')
    item_count = struct.unpack_from('<H', data, 0)[0]
    cursor = 2
    for _ in range(item_count):
        if len(data) - cursor < 4:
            raise ProtocolError('Truncated Common Packet Format item header')
        item_type, item_size = struct.unpack_from('<HH', data, cursor)
        cursor += 4
        if item_size > len(data) - cursor:
            raise ProtocolError('Truncated Common Packet Format item data')
        item = data[cursor:cursor + item_size]
        cursor += item_size
        if item_type != 0x000C:  # ListIdentity identity item
            continue
        # 2 bytes protocol version + 16 bytes sockaddr_in
        if len(item) < 18 + 14 + 1 + 1:
            raise ProtocolError('Truncated identity item')
        family, port = struct.unpack_from('!HH', item, 2)
        if family != 2:  # AF_INET in the network-level SOCKADDR representation
            raise ProtocolError(f'Unsupported identity socket family: {family}')
        device_address = socket.inet_ntoa(item[6:10])
        vendor, device_type, product, major, minor, dev_status, serial = struct.unpack_from('<HHHBBHI', item, 18)
        name_length = item[32]
        if len(item) < 33 + name_length + 1:
            raise ProtocolError('Truncated identity product name or state')
        name = item[33:33 + name_length].decode('utf-8', errors='replace')
        state = item[33 + name_length]
        return Identity(queried_address, device_address, port, vendor, device_type,
                        product, f'{major}.{minor}', dev_status, f'{serial:08X}', name, state)
    if cursor != len(data):
        raise ProtocolError('Trailing Common Packet Format bytes')
    raise ProtocolError('No Identity item found')


def probe(host: str, *, port: int = EIP_PORT, timeout: float = 2.0) -> Identity:
    """Read the target's identity over a *directed* TCP connection, without changing it."""
    host = str(ipaddress.IPv4Address(host))  # No DNS resolution or implicit subnet scanning.
    if not 1 <= port <= 65535:
        raise ValueError('port must be between 1 and 65535')
    if not 0 < timeout <= 30:
        raise ValueError('timeout must be greater than 0 and at most 30 seconds')
    request = ENCAPSULATION_HEADER.pack(LIST_IDENTITY, 0, 0, 0, b'\x00' * 8, 0)
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(request)
        header = _receive_exact(sock, ENCAPSULATION_HEADER.size)
        length = ENCAPSULATION_HEADER.unpack(header)[1]
        if length > MAX_REPLY_LENGTH:
            raise ProtocolError('EtherNet/IP reply exceeds limit')
        payload = _receive_exact(sock, length)
    return decode_list_identity(header, payload, host)


def discover(*, broadcast: str = '255.255.255.255', bind: str = '0.0.0.0',
             port: int = EIP_PORT, timeout: float = 2.0) -> list[Identity]:
    """Explicit one-packet UDP discovery on the chosen network, no subnet sweep.

    Broadcasts may be filtered; a lack of replies does not establish absence.
    """
    broadcast = str(ipaddress.IPv4Address(broadcast))
    bind = str(ipaddress.IPv4Address(bind))
    if not 1 <= port <= 65535:
        raise ValueError('port must be between 1 and 65535')
    if not 0 < timeout <= 30:
        raise ValueError('timeout must be greater than 0 and at most 30 seconds')
    request = ENCAPSULATION_HEADER.pack(LIST_IDENTITY, 0, 0, 0, b'\x00' * 8, 0)
    discovered: dict[tuple[str, str], Identity] = {}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind((bind, 0))
        sock.sendto(request, (broadcast, port))
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            sock.settimeout(remaining)
            try:
                packet, (sender, _) = sock.recvfrom(MAX_REPLY_LENGTH + ENCAPSULATION_HEADER.size + 1)
            except socket.timeout:
                break
            if len(packet) < ENCAPSULATION_HEADER.size:
                continue
            try:
                identity = decode_list_identity(packet[:24], packet[24:], sender)
            except ProtocolError:
                continue
            discovered[(sender, identity.serial_number)] = identity
    return sorted(discovered.values(), key=lambda item: (item.queried_address, item.serial_number))
