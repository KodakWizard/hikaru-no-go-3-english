"""Result-atlas-only candidate: translate existing ink, keep code/palettes."""
from pathlib import Path
import json,struct,shutil
from collections import Counter
from patch_utils import sha
from qa_research_v10 import current_files
from decode_bpe import decode
from encode_bpe import encode
from textures import resources,texture
from smooth_art import write_texture
from result_spacing_v58 import edits,layout_audit,GRIDS,W
from bps_patch import make
R=Path(__file__).resolve().parent
BASE=R/'English_TitleLayers_Test_v57/Hikaru no Go 3 - English Title Layers Test v57.iso'
SOURCE=R/'Hikaru no Go 3 (Japan).iso'
OUT=R/'English_ResultSpacing_Test_v58';assert not OUT.exists();OUT.mkdir()
TARGET=OUT/'Hikaru no Go 3 - English Result Spacing Test v58.iso'
BASE_SHA='e09fdbaa55b0841b6b5d899cec97b2f936659a72c6def307d5c131cee6ec38fa'
SOURCE_SHA='c6882110afa9ef27bf49f2e0530e37c51164d5ad0c10466cb164fc1b938406fc'
assert sha(BASE)==BASE_SHA and sha(SOURCE)==SOURCE_SHA
f,fst,files=current_files(BASE);off,n,index=files['2D/win.bpe'];f.seek(off);original=decode(f.read(n))
# The v55 DOL was relocated: reserve its LIVE extent when allocating new art.
f.seek(0x420);dol_at=int.from_bytes(f.read(4),'big');f.seek(dol_at);header=f.read(0x100)
dol_size=max(struct.unpack_from('>I',header,i*4)[0]+struct.unpack_from('>I',header,0x90+i*4)[0] for i in range(18) if struct.unpack_from('>I',header,0x90+i*4)[0]);f.close()
lookup=dict(resources(original));new=bytearray(original);proposed,changes=edits(original);ranges=[];decoded={}
for name,im in proposed.items():
    at=lookup[name];old,desc=texture(original,at);fmt,w,h,start=desc
    assert fmt==9 and im.size==old.size
    decoded[name]=write_texture(new,at,im)
    assert texture(new,at)[1]==desc
    visible=lambda x:Counter(p for p in x.getdata() if p[3])
    assert visible(decoded[name])==visible(im),(name,'native quantization altered ink')
    assert decoded[name].getchannel('A').tobytes()==im.getchannel('A').tobytes()
    # Includes only padded CI8 texture pixels, never the palette or descriptor.
    end=start+((w+7)//8)*8*((h+3)//4)*4
    ranges.append((start,end));decoded[name].save(OUT/(name+'.png'))
assert len(new)==len(original)
cursor=0
for lo,hi in sorted(ranges):assert original[cursor:lo]==new[cursor:lo];cursor=hi
assert original[cursor:]==new[cursor:]
for name,at in resources(original):
    if name.endswith('.D4') and name not in proposed:
        assert texture(new,at)[0].tobytes()==texture(original,at)[0].tobytes(),name
audit=layout_audit({n:texture(original,lookup[n])[0] for n in GRIDS},decoded)
packed=encode(new,4096);assert decode(packed)==new
placement=(max([o+s for o,s,_ in files.values() if o<1085734912]+[dol_at+dol_size])+0x7fff)&~0x7fff
assert placement+len(packed)<1085734912
inventory=json.loads((R/'translation_work/inventory.json').read_text(encoding='utf8'))
assert all(placement+len(packed)<=e['offset'] or placement>=e['offset']+e['size'] for e in inventory)
assert all(placement+len(packed)<=o or placement>=o+s for o,s,_ in files.values())
assert placement>=dol_at+dol_size
meta=json.loads((R/'translation_work/disc_metadata.json').read_text());oldfst=bytes(fst)
struct.pack_into('>II',fst,index*12+4,placement,len(packed))
assert fst[:index*12+4]==oldfst[:index*12+4] and fst[index*12+12:]==oldfst[index*12+12:]
print('Native glyph pixels and palettes preserved; 9,010 static layout cases passed.',flush=True)
shutil.copyfile(BASE,TARGET)
with TARGET.open('r+b') as g:
    g.seek(meta['fst_offset']);g.write(fst);g.seek(placement);g.write(packed)
f,_,base_files=current_files(BASE);g,got,fs=current_files(TARGET);assert got==fst and len(fs)==len(base_files)==719
for path,(at,s,i) in fs.items():
    g.seek(at);now=g.read(s)
    if path=='2D/win.bpe':assert now==packed and decode(now)==new
    else:
        assert fs[path]==base_files[path];f.seek(at);assert now==f.read(s),path
f.close();g.close()
allowed=sorted([(meta['fst_offset']+index*12+4,meta['fst_offset']+index*12+12),(placement,placement+len(packed))])
with BASE.open('rb') as f,TARGET.open('rb') as g:
    pos=0
    while True:
        a=f.read(8*1024*1024);b=g.read(8*1024*1024)
        if not a:assert not b;break
        assert len(a)==len(b);cursor=0
        for lo,hi in allowed:
            aa=max(0,lo-pos);bb=min(len(a),hi-pos)
            if aa<bb:assert a[cursor:aa]==b[cursor:aa];cursor=bb
        assert a[cursor:]==b[cursor:];pos+=len(a)
print('All 719 active files checked; whole-disc changes limited to win archive and eight-byte FST entry.',flush=True)
target_sha=sha(TARGET)
patch=make(SOURCE,TARGET,OUT/'Hikaru_no_Go_3_English_ResultSpacing_Test_v58.bps',dict(game='Hikaru no Go 3',version='internal test v58',base='Original Japanese GHTJA4'))
assert sha(BASE)==BASE_SHA and sha(SOURCE)==SOURCE_SHA
report=dict(version='internal test v58',source_sha256=SOURCE_SHA,previous_sha256=BASE_SHA,output_sha256=target_sha,
            modified_active_files=['2D/win.bpe'],modified_images=list(proposed),
            atlas_changes=changes,layout_audit=audit,decoded_archive_bytes=len(new),stored_archive_bytes=len(packed),
            placement=placement,live_dol_extent_reserved=[dol_at,dol_at+dol_size],
            native_formats_dimensions_palettes_descriptors_unchanged=True,
            existing_visible_rgba_pixels_preserved=True,no_resampling_new_outline_or_halo=True,
            all719_active_files_checked=True,whole_disc_comparison_passed=True,
            code_fonts_title_dialogue_scripts_saves_exact_v57=True,patch=patch,
            status='Local test only; Dolphin result appearance/exit testing pending; GitHub remains Version1.0.1.')
(OUT/'build_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
shutil.copyfile(W/'result_spacing_comparison.png',OUT/'result_spacing_comparison.png')
(OUT/'README.md').write_text('''# Results spacing test v58

Based on public Version 1.0.1 / v57. Only six existing result atlases change.
The already-rendered glyph pixels are moved within original cells, with the same
palette and no font redraw, scaling, stroke, blur or halo. All result labels use
a common baseline. Time/Resign ink is moved left within its native reason cell;
Draw/Jigo start at a consistent inset. Existing Win/Loss and numeric cells retain
their horizontal positions. All code, title, fonts, dialogue and saves are exact
v57. Live relocated DOL extent was explicitly reserved when placing the archive.

9,010 static placement checks cover both colours, Win/Loss, Time/Resign, Draw/Jigo,
0..999 integer and half-point margins and 0..999 move counts. Decoded coverage
shows at least 12 native pixels between result tokens (was -5 in the old layout).
These are static atlas checks, not emulator gameplay or proof of all animation
phases. The comparison image is a static rendering, not a Dolphin screenshot.

Preserved limitations: move-count digits still use native fixed advances. Lower
score formatting still places pt before .5; this pre-existing formatting issue
is separate from the artwork overlap correction. No code change was made to
rewrite result assembly. Large score fields/top player panels are unchanged.

Cold boot; test opponent resignation and own resignation (both colours); time-out,
draw/jigo and an integer/half-point result if reachable. Check the results screen
accepts exit input and the next dialogue/menu works. No GitHub update yet.
''',encoding='utf8')
print('Built',TARGET,target_sha,flush=True)
