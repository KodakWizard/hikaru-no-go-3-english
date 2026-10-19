"""Small deterministic checks for the portable public tools."""
import json,struct,tempfile,unittest,zlib
from pathlib import Path
from unittest.mock import patch
import project

def number(n):
    result=bytearray()
    while True:
        b=n&127;n>>=7
        if not n:result.append(b|128);return result
        result.append(b);n-=1

def fixture():
    # SourceRead two bytes, TargetRead two bytes, SourceRead four bytes.
    b=bytearray(b'BPS1')+number(8)+number(8)+number(0)
    b+=number(4)+number(5)+b'XY'+number(12)
    b+=struct.pack('<II',zlib.crc32(b'abcdefgh'),zlib.crc32(b'abXYefgh'))
    return bytes(b+struct.pack('<I',zlib.crc32(b)))

class PortableTools(unittest.TestCase):
    def test_commands(self):
        self.assertEqual(list(project.patch_commands(fixture(),8)),[(0,2,None),(2,2,b'XY'),(4,4,None)])
    def test_corruption(self):
        data=bytearray(fixture());data[5]^=1
        with self.assertRaises(ValueError):list(project.patch_commands(data,8))
    def test_wrong_size(self):
        with self.assertRaises(ValueError):list(project.patch_commands(fixture(),9))
    def test_truncation(self):
        with self.assertRaises(ValueError):list(project.patch_commands(fixture()[:10],8))
    def test_wrong_source_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'source').write_bytes(b'wrong')
            with self.assertRaises(ValueError):project.apply(p/'source',p/'absent-patch',p/'out')
            self.assertFalse((p/'out').exists())
    def check_edit_rejection(self,after,message):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);source=bytearray(0x500);struct.pack_into('>III',source,0x420,0x450,0x440,12)
            struct.pack_into('>III',source,0x440,0x01000000,0,1)
            source[0x460:0x468]=b'Hi $0!\0\0'
            (p/'source').write_bytes(source)
            catalog=[dict(id='test',area='dol',offset=16,baseline='Hi $0!',english=after,capacity_bytes=6,line_budget=[18,3],line_break='↓')]
            (p/'catalog').write_text(json.dumps(catalog),encoding='utf8')
            with patch.object(project,'TARGET_SHA',project.sha(p/'source')):
                with self.assertRaisesRegex(ValueError,message):project.edit(p/'source',p/'catalog',p/'out')
            self.assertFalse((p/'out').exists())
    def test_oversize_text(self):self.check_edit_rejection('Hello there $0!','capacity')
    def test_placeholder_loss(self):self.check_edit_rejection('Hi!','placeholders')
    def test_embedded_null(self):self.check_edit_rejection('$0\0','null')

if __name__=='__main__':unittest.main()
