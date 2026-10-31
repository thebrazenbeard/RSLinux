import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
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

    def test_rejects_utf16_internal_entities(self):
        document = ('<?xml version="1.0" encoding="UTF-16"?>'
                    '<!DOCTYPE RSLogix5000Content [<!ENTITY boom "expanded">]>'
                    '<RSLogix5000Content>&boom;</RSLogix5000Content>')
        for codec in ('utf-16', 'utf-16-le', 'utf-16-be'):
            with self.subTest(codec=codec):
                with self.assertRaisesRegex(ValueError, 'DTD/entity'):
                    self._load(document.encode(codec))

    def test_rejects_utf16_external_doctype(self):
        document = ('<?xml version="1.0" encoding="UTF-16"?>'
                    '<!DOCTYPE RSLogix5000Content SYSTEM "file:///etc/passwd">'
                    '<RSLogix5000Content/>')
        with self.assertRaisesRegex(ValueError, 'DTD/entity'):
            self._load(document.encode('utf-16'))

    def test_accepts_utf16_without_dtd(self):
        document = SAMPLE.decode('utf-8').replace('encoding="UTF-8"', 'encoding="UTF-16"')
        for codec in ('utf-16', 'utf-16-le', 'utf-16-be'):
            with self.subTest(codec=codec):
                self.assertEqual(self._load(document.encode(codec))['all_tag_count'], 3)

    def test_dtd_like_text_in_comment_does_not_trigger_false_positive(self):
        document = b'<RSLogix5000Content><!-- <!DOCTYPE fake> --></RSLogix5000Content>'
        self.assertEqual(self._load(document)['all_tag_count'], 0)

    def test_rejects_malformed_xml(self):
        with self.assertRaises(ET.ParseError):
            self._load(b'<RSLogix5000Content><Controller>')

    def test_rejects_file_larger_than_limit(self):
        with patch('rslinux5000000.l5x.MAX_FILE_BYTES', len(SAMPLE) - 1):
            with self.assertRaisesRegex(ValueError, 'inspection limit'):
                self._load(SAMPLE)

    def test_read_is_bounded_if_file_grows_after_precheck(self):
        class RecordingStream(io.BytesIO):
            def __init__(self, payload):
                super().__init__(payload)
                self.requested_sizes = []

            def read(self, size=-1):
                self.requested_sizes.append(size)
                if size < 0:
                    raise AssertionError('unbounded file read')
                return super().read(size)

        stream = RecordingStream(SAMPLE + b'oversize')
        maximum = len(SAMPLE) - 1
        with patch.object(Path, 'is_file', return_value=True), \
             patch.object(Path, 'stat', return_value=SimpleNamespace(st_size=0)), \
             patch.object(Path, 'open', return_value=stream), \
             patch('rslinux5000000.l5x.MAX_FILE_BYTES', maximum):
            with self.assertRaisesRegex(ValueError, 'inspection limit'):
                summarize('simulated-growth.l5x')
        self.assertEqual(stream.requested_sizes, [maximum + 1])
