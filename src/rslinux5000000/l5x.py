"""Read-only high-level inventory of Logix XML exports (.L5X)."""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

MAX_FILE_BYTES = 64 * 1024 * 1024


class _NoDTDTreeBuilder(ET.TreeBuilder):
    """Reject DTDs at the XML parser event boundary, for any XML encoding."""

    def doctype(self, name: str, pubid: str | None, system: str | None) -> None:
        raise ValueError('DTD/entity declarations are not accepted')


def _local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def _names(parent: ET.Element, child_name: str) -> list[str]:
    return sorted({e.attrib['Name'] for e in parent.iter()
                   if _local_name(e.tag) == child_name and e.attrib.get('Name')})


def summarize(path: str | Path) -> dict:
    file = Path(path)
    if not file.is_file():
        raise ValueError(f'Not a file: {file}')
    if file.stat().st_size > MAX_FILE_BYTES:
        raise ValueError('L5X file exceeds 64 MiB inspection limit')
    data = file.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise ValueError('L5X file exceeds 64 MiB inspection limit')
    root = ET.fromstring(data, parser=ET.XMLParser(target=_NoDTDTreeBuilder()))
    if _local_name(root.tag) != 'RSLogix5000Content':
        raise ValueError('XML root is not RSLogix5000Content')
    controllers = [node for node in root.iter() if _local_name(node.tag) == 'Controller']
    controller = controllers[0] if controllers else None
    tags = [node for node in root.iter() if _local_name(node.tag) == 'Tag']
    ctl_tags = []
    for node in root.iter():
        if _local_name(node.tag) == 'Controller':
            for child in node:
                if _local_name(child.tag) == 'Tags':
                    ctl_tags += [t.attrib['Name'] for t in child
                                 if _local_name(t.tag) == 'Tag' and t.attrib.get('Name')]
    return {
        'format': 'L5X',
        'schema_revision': root.attrib.get('SchemaRevision'),
        'software_revision': root.attrib.get('SoftwareRevision'),
        'target_type': root.attrib.get('TargetType'),
        'controller': {
            'name': controller.attrib.get('Name'),
            'processor_type': controller.attrib.get('ProcessorType'),
            'major_revision': controller.attrib.get('MajorRev'),
            'minor_revision': controller.attrib.get('MinorRev'),
        } if controller is not None else None,
        'programs': _names(root, 'Program'),
        'routines': _names(root, 'Routine'),
        'modules': _names(root, 'Module'),
        'all_tag_count': len(tags),
        'controller_tag_names': sorted(set(ctl_tags)),
    }
