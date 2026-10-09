# RSLinux5000000 — Capability boundaries

1. **Discovery (implemented as a prototype)**: directed TCP and explicit UDP broadcast EtherNet/IP ListIdentity queries. This tells us the Ethernet endpoint's advertised identity, not whether an online RSLogix session or a program upload is possible. No automatic scanning.
2. **Online inspection (not implemented)**: controller firmware and chassis identification, tag enumeration and optional read-only tag values, with explicit user target selection. Evaluate pycomm3, pylogix, or libplctag rather than rolling an unreviewed tag protocol stack.
3. **Offline L5X file inspection (basic inventory implemented)**: preserve unknown XML, scopes, module tree, tags, AOIs, structured text and ladder representation. Treat source-protected blocks as opaque. L5X XML is not an .ACD editor or a way to upload arbitrary live controller logic.
4. **Editing, download and motion/I/O control (not implemented)**: inherently higher risk. No claim that a complete Logix 5000 project upload/download is implementable from the sources provided; needs documented protocol paths, device/firmware-specific qualification, backups, safety boundaries, and separate user authorization.

## Testability

Protocol packet decoding is separated from sockets. Tests can supply fixed EtherNet/IP reply bytes and a local mock server. Live hardware verification is a separate evidence class and remains unperformed.

## Licensing

The supplied L5X Python library is GPLv3+ whereas ioList and the EthernetIP-Simulator advertise MIT. Dependency import vs copying/derivation has separate legal implications; choose a project license before incorporating third-party code. No third-party source copied here.
