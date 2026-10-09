import tempfile
import unittest
from pathlib import Path
from rslinux5000000.l5x import summarize

SAMPLE = b'''<?xml version="1.0" encoding="UTF-8"?>
<RSLogix5000Content SchemaRevision="1.0" SoftwareRevision="20.00" TargetType="Controller">
  <Controller Name="TestPLC" ProcessorType="1769-L32E" MajorRev="20" MinorRev="13">
    <Tags><Tag Name="Start" DataType="BOOL"/><Tag Name="Count" DataType="DINT"/></Tags>
    <Modules><Module Name="LocalENet"/></Modules>
    <Programs><Program Name="Main"><Tags><Tag Name="Timer" DataType="TIMER"/></Tags>
      <Routines><Routine Name="Routine0" Type="RLL"/></Routines></Program></Programs>
  </Controller>
</RSLogix5000Content>'''


class L5XTest(unittest.TestCase):
    def _load(self, data):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'sample.L5X'
            path.write_bytes(data)
            return summarize(path)

    def test_inventory(self):
        result = self._load(SAMPLE)
        self.assertEqual(result['controller']['processor_type'], '1769-L32E')
        self.assertEqual(result['programs'], ['Main'])
        self.assertEqual(result['routines'], ['Routine0'])
        self.assertEqual(result['modules'], ['LocalENet'])
        self.assertEqual(result['all_tag_count'], 3)
        self.assertEqual(result['controller_tag_names'], ['Count', 'Start'])

    def test_rejects_unrelated_xml(self):
        with self.assertRaises(ValueError):
            self._load(b'<a/>')

    def test_rejects_entities(self):
        with self.assertRaises(ValueError):
            self._load(b'<!DOCTYPE a [<!ENTITY boom "bad">]><RSLogix5000Content/>')
