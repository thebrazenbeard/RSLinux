"""CLI entrypoint for safe inspection of CompactLogix identity and .L5X exports."""
from __future__ import annotations

import argparse
import json
import socket
import sys
import xml.etree.ElementTree as ET

from .eip import ProtocolError, probe, discover
from .l5x import summarize


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='rslinux', description='Read-only Logix inspection tools')
    subparsers = parser.add_subparsers(dest='command', required=True)
    p_probe = subparsers.add_parser('probe', help='Read EtherNet/IP identity over TCP')
    p_probe.add_argument('ipv4', help='Known target IPv4 address')
    p_probe.add_argument('--port', type=int, default=44818)
    p_probe.add_argument('--timeout', type=float, default=2.0)
    p_discovery = subparsers.add_parser('discover', help='Send one explicit UDP ListIdentity discovery request')
    p_discovery.add_argument('--broadcast', default='255.255.255.255', help='Broadcast destination (on an isolated bench LAN)')
    p_discovery.add_argument('--bind', default='0.0.0.0', help='Local IPv4 interface address to send from')
    p_discovery.add_argument('--port', type=int, default=44818)
    p_discovery.add_argument('--timeout', type=float, default=2.0)
    p_l5x = subparsers.add_parser('l5x-summary', help='Summarize a local .L5X export')
    p_l5x.add_argument('file')
    args = parser.parse_args(argv)
    try:
        if args.command == 'probe':
            result = probe(args.ipv4, port=args.port, timeout=args.timeout).as_dict()
        elif args.command == 'discover':
            result = [x.as_dict() for x in discover(broadcast=args.broadcast, bind=args.bind, port=args.port, timeout=args.timeout)]
        else:
            result = summarize(args.file)
    except (OSError, ValueError, ProtocolError, ET.ParseError) as exc:
        print(f'rslinux: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0
