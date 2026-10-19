"""Title-only test from v56; two existing RGBA8 slots, no code/text changes."""
from pathlib import Path
import json, shutil, struct
from patch_utils import sha
from qa_research_v10 import current_files
from decode_bpe import decode
from encode_bpe import encode
from textures import resources, texture
from archive_edit import rgba_resource
from title_layers_v57 import artwork, WORK
from bps_patch import make

R = Path(__file__).resolve().parent
BASE = R/'English_DialogueLayout_v56/Hikaru no Go 3 - English Dialogue Layout v56.iso'
SOURCE = R/'Hikaru no Go 3 (Japan).iso'
OUT = R/'English_TitleLayers_Test_v57'
assert not OUT.exists(), 'Never overwrite a previous test build'
OUT.mkdir()
TARGET = OUT/'Hikaru no Go 3 - English Title Layers Test v57.iso'
base_sha = '372cc172e7ed33fe0d5313f8ed6c5c94e6152700954e571b802a6abbb14cdf87'
source_sha = 'c6882110afa9ef27bf49f2e0530e37c51164d5ad0c10466cb164fc1b938406fc'
assert sha(BASE) == base_sha and sha(SOURCE) == source_sha
print('Original and v56 hashes verified.', flush=True)
f, fst, files = current_files(BASE)
off, size, index = files['title/title.bpe']
f.seek(off)
original = decode(f.read(size))
f.close()
lookup = dict(resources(original))
changes, art_report = artwork(texture(original, lookup['tit00.D4'])[0])
new = bytearray(original)
ranges = []
for name, im in changes.items():
    at = lookup[name]
    old, desc = texture(original, at)
    fmt, w, h, start = desc
    assert (fmt, w, h) == (6, 640, 480) and im.size == old.size
    raw = rgba_resource(original, at, im)
    n = len(raw) - 64
    new[start:start+n] = raw[64:]
    readback, after_desc = texture(new, at)
    assert after_desc == desc and readback.tobytes() == im.tobytes()
    im.save(OUT/(name + '.png'))
    ranges.append((start, start+n))
assert len(new) == len(original)
cursor = 0
for lo, hi in sorted(ranges):
    assert original[cursor:lo] == new[cursor:lo]
    cursor = hi
assert original[cursor:] == new[cursor:]
assert list(resources(new)) == list(resources(original))
for name, at in resources(original):
    if name.endswith('.D4') and name not in changes:
        assert texture(original, at)[0].tobytes() == texture(new, at)[0].tobytes(), name
packed = encode(new, 4096)
assert decode(packed) == new
placement = (max(o+n for o,n,_ in files.values() if o < 1085734912)+0x7fff)&~0x7fff
assert placement + len(packed) < 1085734912
inventory = json.loads((R/'translation_work/inventory.json').read_text(encoding='utf8'))
assert all(placement+len(packed) <= e['offset'] or placement >= e['offset']+e['size'] for e in inventory)
assert all(placement+len(packed) <= o or placement >= o+n for o,n,_ in files.values())
metadata = json.loads((R/'translation_work/disc_metadata.json').read_text())
old_fst = bytes(fst)
struct.pack_into('>II', fst, index*12+4, placement, len(packed))
assert old_fst[:index*12+4] == fst[:index*12+4]
assert old_fst[index*12+12:] == fst[index*12+12:]
print('Two native RGBA8 title images encoded; all descriptors, sprites and archive layout preserved.', flush=True)
shutil.copyfile(BASE, TARGET)
with TARGET.open('r+b') as g:
    g.seek(metadata['fst_offset']); g.write(fst)
    g.seek(placement); g.write(packed)
g, got_fst, fs = current_files(TARGET)
f, _, base_files = current_files(BASE)
assert got_fst == fst and len(fs) == len(base_files) == 719
for path, (at,n,idx) in fs.items():
    g.seek(at); actual = g.read(n)
    if path == 'title/title.bpe':
        assert actual == packed and decode(actual) == new
    else:
        assert fs[path] == base_files[path]
        f.seek(at); assert actual == f.read(n), path
g.close(); f.close()
allowed = sorted([(metadata['fst_offset']+index*12+4, metadata['fst_offset']+index*12+12),
                  (placement, placement+len(packed))])
with BASE.open('rb') as f, TARGET.open('rb') as g:
    pos = 0
    while True:
        a = f.read(8*1024*1024); b = g.read(8*1024*1024)
        if not a: assert not b; break
        assert len(a) == len(b)
        cursor = 0
        for lo,hi in allowed:
            aa=max(0,lo-pos); bb=min(len(a),hi-pos)
            if aa<bb:
                assert a[cursor:aa] == b[cursor:aa]
                cursor=bb
        assert a[cursor:] == b[cursor:]
        pos += len(a)
print('All 719 active files checked; whole-disc comparison permits only title archive and one FST entry.', flush=True)
target_sha = sha(TARGET)
patch = make(SOURCE, TARGET, OUT/'Hikaru_no_Go_3_English_TitleLayers_Test_v57.bps',
             {'game':'Hikaru no Go 3','version':'internal test v57','base':'Original Japanese GHTJA4'})
assert sha(BASE) == base_sha and sha(SOURCE) == source_sha
report = dict(version='internal test v57', source_sha256=source_sha,
              previous_sha256=base_sha, output_sha256=target_sha,
              modified_active_files=['title/title.bpe'], modified_images=list(changes),
              decoded_archive_bytes=len(new), stored_archive_bytes=len(packed),
              placement=placement, native_dimensions_formats_descriptors_unchanged=True,
              code_fonts_dialogue_scripts_saves_unchanged=True,
              all_719_active_files_checked=True, whole_disc_comparison_passed=True,
              original_and_v56_preserved=True, artwork=art_report, patch=patch,
              status='Title-only candidate; cold-boot Dolphin visual/animation test pending. GitHub release unchanged.')
(OUT/'build_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
(OUT/'TESTING.txt').write_text('Cold boot this separate test ISO. Check straight white edges in Push Start and menu states; transitions; Go-board overlay behind logo; animated Story/Free Match states and selection. Game content is otherwise identical to v56/Version 1. Public GitHub release is unchanged.\n',encoding='utf8')
print('Built', TARGET, target_sha, flush=True)
