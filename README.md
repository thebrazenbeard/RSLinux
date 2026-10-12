# RSLinux — Research prototype 0.1

This is a **read-only Python starter**, aimed first at a Rockwell Automation CompactLogix 1769-L32E. It is **not** a replacement for RSLogix 5000 or Studio 5000, not a controller program uploader, and has **not** been tested against physical PLC hardware.

## What works

- `discover`: Send one explicitly requested EtherNet/IP UDP ListIdentity discovery broadcast, collect replies for a bounded interval. No IP-range sweep; run only on an isolated bench network.
- `probe`: Send EtherNet/IP encapsulation **ListIdentity** (0x0063) to a *known* IPv4 address over TCP port 44818. Decode product name, vendor, device type, code, firmware major/minor, and serial. Does not register an EtherNet/IP session or send tag writes, downloads, mode changes, or firmware commands.
- `l5x-summary`: Inspect a local exported `.L5X` (Logix XML) without changing it. Reports controller, programs, routines, module names and tag count. This operates on an exported **file**, not the program residing in the PLC.

## Requirements and installation

Python 3.10+ (Linux, Windows, or macOS). No third-party dependencies for the commands.

Install from this GitHub repository with `python -m pip install git+https://github.com/thebrazenbeard/RSLinux5000000.git`, or clone it and run `python -m pip install .` in the checkout. The installed `rslinux` command supports `discover`, `probe`, and `l5x-summary`. The `PYTHONPATH=src` commands below also work without installation from a checkout.

In the project directory:

```bash
PYTHONPATH=src python -m rslinux5000000 discover --bind 192.168.1.2
PYTHONPATH=src python -m rslinux5000000 probe 192.168.1.10
PYTHONPATH=src python -m rslinux5000000 l5x-summary exported.L5X
PYTHONPATH=src python -m unittest discover -s tests -v
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = 'src'
python -m rslinux5000000 probe 192.168.1.10
```

Replace `192.168.1.2` with your laptop Ethernet interface IPv4 and `192.168.1.10` with the PLC's **actual** IP address. A timeout does not establish that the device is absent: its IP may be on a different subnet, BOOTP may be active, a firewall may be blocking traffic, or the hardware may be unpowered. Do not reset or change the PLC IP just to make this probe work.

## Safety and scope

Use only with authorized equipment on an isolated test bench. Do not connect a bench PLC with unknown ladder logic to active machinery or the plant network. Confirm compatible 1769 power supply, wiring, end cap, and grounding from the correct Rockwell manual. Before any programming later, save a backup and independently verify controller mode, firmware version and ownership of the logic.

Read-only network requests still interact with embedded devices; do not equate absence of write commands with formal safety qualification. This tool neither bypasses source protection nor imports protected code. `.ACD` binaries are not `.L5X` XML exports and are not supported.

## Sources assessed

- [jvalenzuela/l5x](https://github.com/jvalenzuela/l5x) — broad `.L5X` tag/file manipulation; GPLv3+, **not incorporated** into this prototype.
- [tnunnink/ioList](https://github.com/tnunnink/ioList) — Windows WPF L5X-based I/O list generator; MIT; concept useful for later exports.
- [faraquet/RSLogix5000-Tag-Generator](https://github.com/faraquet/RSLogix5000-Tag-Generator) — legacy Python 2 tag CSV creation; no source incorporated.
- [imdtouch/EthernetIP-Simulator](https://github.com/imdtouch/EthernetIP-Simulator) — EtherNet/IP virtual device/server; MIT, different goal from controller program upload.
- [skdatmonster/DecryptSourceProtection](https://github.com/skdatmonster/DecryptSourceProtection) — source-protection removal; **not incorporated** and not needed for initial connectivity.
- [ottowayi/pycomm3](https://github.com/ottowayi/pycomm3) — possible future Logix tag browsing/reading backend; its own repository cautions that development has ceased.
- [dmroeder/pylogix](https://github.com/dmroeder/pylogix) — another Logix communication library to evaluate.
- [libplctag/libplctag](https://github.com/libplctag/libplctag) — native cross-platform tag communication candidate.

No third-party source code has been copied. A project-wide license has **not** been selected.
