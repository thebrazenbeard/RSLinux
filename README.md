# RSLinux — read-only EtherNet/IP and Logix export inspection

**RSLinux is a small, cross-platform Python inspection toolkit for industrial-controller identity and exported Logix XML metadata.** It provides explicitly requested EtherNet/IP ListIdentity probes and a local `.L5X` summary command without a controller programming or write interface.

**Status:** research prototype `0.1.0`, initially exercised against a CompactLogix 1769-L32E-oriented test model. No physical PLC qualification has been demonstrated. It is **not** RSLogix 5000 or Studio 5000, a controller-program uploader, a source-protection bypass, or a plant-safety system.

## Capabilities and boundaries

| CLI command | Input | Output and effect boundary |
| --- | --- | --- |
| `rslinux l5x-summary` | A local `.L5X` XML export | JSON inventory of controller/program/routine/module names and tag counts; does not contact a PLC or modify the file. Rejects files over 64 MiB and DTD/entity declarations. |
| `rslinux probe` | One explicitly supplied IPv4 address | Sends EtherNet/IP encapsulation **ListIdentity** (`0x0063`) over TCP (default port 44818); reports identity fields such as vendor, device type, product code/name, revision and serial. No DNS name, subnet sweep, CIP session, tag access, download or configuration write. |
| `rslinux discover` | An explicitly selected isolated bench network | Sends one UDP ListIdentity broadcast and collects replies within a bounded timeout. This is a network interaction even though it does not issue PLC writes. No IP-range scan. |

The package uses Python **3.10+**, its standard library and the installed `rslinux` command. There are no runtime third-party Python dependencies declared in `pyproject.toml`.

## Install and inspect locally

From a permitted repository checkout:

```bash
python -m pip install .
rslinux --help
rslinux l5x-summary exported.L5X   # replace with a real local export
python -m unittest discover -s tests -v
```

An `.ACD` controller project is **not** an `.L5X` XML export and is not accepted by the XML summarizer. Obtain any export through authorized engineering software and existing change-control procedures.

For development without installing the entrypoint, the equivalent module form is:

```bash
PYTHONPATH=src python -m rslinux5000000 l5x-summary exported.L5X
```

## Optional network identity inspection (authorized bench only)

The addresses below come from the **documentation-only** IPv4 ranges in RFC 5737. They are placeholders, not configured devices or working interface addresses. **Replace them with the actual permitted IP addresses on an isolated test bench before running either command.** Never run discovery on a production or shared network.

```bash
# Documentation placeholders; configure for your own authorized bench first.
BENCH_INTERFACE_IP=198.51.100.2
BENCH_PLC_IP=203.0.113.10

rslinux probe "$BENCH_PLC_IP" --timeout 2
rslinux discover --bind "$BENCH_INTERFACE_IP" --timeout 2
```

Windows PowerShell uses the same installed command:

```powershell
# Documentation-only placeholder: replace with your authorized bench PLC IPv4.
$BenchPlcIp = '203.0.113.10'
rslinux probe $BenchPlcIp --timeout 2
```

A timeout is not proof that a device is absent: subnet differences, BOOTP, firewalls, power state and filtered broadcasts can all prevent a response. Do **not** reset or change a controller IP merely to make this probe work.

## Safety and licensing

- Operate only on equipment and networks you are authorized to inspect, ideally an isolated lab bench. Do not attach a controller with unknown logic to active machinery or a plant network.
- Before any future programming work, follow the applicable Rockwell hardware/manual requirements for power, wiring, grounding, end caps and safety procedures; preserve backups and independently verify firmware, controller mode and logic ownership.
- Read-only network traffic still interacts with embedded devices. No write command in this implementation is **not** equivalent to physical safety qualification.
- The repository does not include copied third-party source. **No project-wide license has been selected**; public GitHub visibility should not be mistaken for a grant of reuse or redistribution rights.

## Research sources assessed (not incorporated)

- [jvalenzuela/l5x](https://github.com/jvalenzuela/l5x) — broad `.L5X` tag/file manipulation; GPLv3+, not incorporated.
- [tnunnink/ioList](https://github.com/tnunnink/ioList) — Windows WPF L5X-based I/O list generator; MIT, concept reference.
- [faraquet/RSLogix5000-Tag-Generator](https://github.com/faraquet/RSLogix5000-Tag-Generator) — legacy Python 2 tag CSV creation; no source incorporated.
- [imdtouch/EthernetIP-Simulator](https://github.com/imdtouch/EthernetIP-Simulator) — EtherNet/IP virtual-device/server project; MIT, different scope.
- [skdatmonster/DecryptSourceProtection](https://github.com/skdatmonster/DecryptSourceProtection) — source-protection removal; not incorporated and not required for identity inspection.
- [ottowayi/pycomm3](https://github.com/ottowayi/pycomm3), [dmroeder/pylogix](https://github.com/dmroeder/pylogix), [libplctag/libplctag](https://github.com/libplctag/libplctag) — possible future Logix communication references, not runtime dependencies of this prototype.

## Editor-startup source safety

The tracked repository has no VS Code `folderOpen` execution task or disguised executable asset previously associated with one. `tests/test_editor_startup_safety.py` checks the known source configuration and asset absence. User/application-level editor automatic-task settings remain outside repository control.

Those checks do not prove that older checkouts, installed packages, a workstation, a PLC network, or physical machinery are safe. No live PLC test or deployment qualification is implied.
