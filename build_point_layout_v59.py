"""Half-point result display only; replace one existing 31-word block."""
from pathlib import Path
import json,struct,shutil
from PIL import Image,ImageDraw
from point_layout_v59 import patch,validate,execute,sections,offset,PATCH
from qa_research_v10 import current_files
from patch_utils import sha
from bps_patch import make
R=Path(__file__).resolve().parent
BASE=R/'English_ResultSpacing_Test_v58/Hikaru no Go 3 - English Result Spacing Test v58.iso'
SOURCE=R/'Hikaru no Go 3 (Japan).iso'
OUT=R/'English_PointLayout_Test_v59';OUT.mkdir(exist_ok=True)
W=R/'translation_work/point_layout_v59';W.mkdir(exist_ok=True)
TARGET=OUT/'Hikaru no Go 3 - English Point Layout Test v59.iso'
assert not TARGET.exists(), 'Never overwrite a test ISO'
BASE_SHA='9f291e51f146958dc2bd351d2c78eada17fa8ff54a8b27d7d5266753b27d71f8'
SOURCE_SHA='c6882110afa9ef27bf49f2e0530e37c51164d5ad0c10466cb164fc1b938406fc'
assert sha(BASE)==BASE_SHA and sha(SOURCE)==SOURCE_SHA
with BASE.open('rb') as f:
    f.seek(0x420);dol_at=int.from_bytes(f.read(4),'big');f.seek(dol_at);header=f.read(0x100)
    size=max(o+n for _,o,a,n in sections(header));f.seek(dol_at);before=f.read(size)
after,changes=patch(before);checks=validate(before,after)
assert before[:0x100]==after[:0x100] and len(after)==len(before)
ranges=sorted((offset(before,a),offset(before,a)+4) for a in PATCH)
cursor=0
for lo,hi in ranges:assert before[cursor:lo]==after[cursor:lo];cursor=hi
assert before[cursor:]==after[cursor:]
# Audit references in actual live executable sections, including the v55 helper.
from point_layout_v59 import MD
MD.skipdata=True
calls=[]
for i,o,a,n in sections(before):
    if i>=7:continue
    for ins in MD.disasm(before[o:o+n],a):
        if ins.mnemonic in ('bl','b') and ins.op_str=='0x8012e8b8':calls.append(ins.address)
assert calls==[0x8012df0c,0x8012df84,0x8012e350,0x8012e3cc],[hex(x) for x in calls]
# The sole absolute address is the compiler's exception-unwind index, not a
# dispatch table: {function start, byte length, exception-table pointer}.
literal=bytes.fromhex('8012e8b8')
locations=[i for i in range(len(before)-3) if before[i:i+4]==literal]
assert locations==[0x229448],locations
assert struct.unpack_from('>III',before,locations[0])==(0x8012e8b8,0x888,0x8000a664)
assert 0x8012e8b8+0x888==0x8012f140
assert before[0x229448:0x229454]==after[0x229448:0x229454]
# Original early Y initialization must remain byte-exact.
original=(R/'translation_work/main.dol').read_bytes()
for lo,hi in [(0x8012e978,0x8012e9f0),(0x8012ed14,0x8012ed4c),(0x8012f04c,0x8012f054),(0x8012f0d4,0x8012f140)]:
    assert before[offset(before,lo):offset(before,hi)]==original[offset(original,lo):offset(original,hi)]
    assert after[offset(after,lo):offset(after,hi)]==before[offset(before,lo):offset(before,hi)]
checks.update(direct_callers=[hex(x) for x in calls],
              all_direct_callers_in_result_screen_setter=True,
              only_absolute_reference_is_unchanged_exception_unwind_index=True,
              original_early_y_initialization_exact=True,
              no_branch_call_helper_allocation_or_data_constant_changes=True)
print('8,000 original/patched PPC display-block cases pass; only half-result X coordinates differ.',flush=True)
# Render existing v58 sprites at coordinates produced by executing actual words.
atlas={name:Image.open(R/'English_ResultSpacing_Test_v58'/name).convert('RGBA')
       for name in ['win43_2.D4.png','win43_3.D4.png','win43_4.D4.png']}
def cell(name,i,cw):return atlas[name].crop((i*cw,0,(i+1)*cw,42))
rows=[(0,0,True,0),(1,6,True,0),(0,11,True,1),(1,101,True,1),(1,999,True,0),(1,6,False,0)]
sheet=Image.new('RGBA',(960,70+len(rows)*65),(55,55,55,255));draw=ImageDraw.Draw(sheet)
draw.text((8,8),'Static native-sprite preview from offline PPC positions. BEFORE (left) / AFTER (right).',fill='white')
min_decimal=999;min_unit=999;min_outcome=999
for index,(side,margin,half,outcome) in enumerate(rows):
    y=65+index*65;end=103+38+29*(len(str(margin))-1)
    draw.text((8,y-13),f'{"W" if side==0 else "B"} {margin}{".5" if half else ""} pt {"Win" if outcome==0 else "Loss"}',fill='white')
    for col,dol in [(0,before),(480,after)]:
        state,_,_=execute(dol,end,int(half))
        sheet.alpha_composite(cell('win43_2.D4.png',side,38),(col+65,y))
        for i,d in enumerate(str(margin)):sheet.alpha_composite(cell('win43_3.D4.png',int(d),38),(col+106+29*i,y))
        for field,im in [('0x44',cell('win43_2.D4.png',2,38)),('0x48',cell('win43_2.D4.png',3,38)),('0x58',cell('win43_4.D4.png',outcome,68))]:
            if not state[field]['hidden'] or field in ('0x44','0x58'):
                x=round(state[field]['x']-state[field]['width']/2)
                sheet.alpha_composite(im,(col+x,y))
for margin in range(1000):
    end=103+38+29*(len(str(margin))-1)
    s,_,_=execute(after,end,1)
    digitbox=cell('win43_3.D4.png',int(str(margin)[-1]),38).getchannel('A').getbbox()
    halfbox=cell('win43_2.D4.png',3,38).getchannel('A').getbbox()
    ptbox=cell('win43_2.D4.png',2,38).getchannel('A').getbbox()
    hx=s['0x48']['x']-19;px=s['0x44']['x']-19;wx=s['0x58']['x']-34
    dg=hx+halfbox[0]-(end-35+digitbox[2]);ug=px+ptbox[0]-(hx+halfbox[2])
    for win in (0,1):
        wb=cell('win43_4.D4.png',win,68).getchannel('A').getbbox()
        gap=wx+wb[0]-(px+ptbox[2]);assert gap>=12
        min_outcome=min(min_outcome,gap)
    assert 2<=dg<=6 and ug>=6
    min_decimal=min(min_decimal,dg);min_unit=min(min_unit,ug)
checks.update(minimum_decimal_gap=min_decimal,minimum_unit_gap=min_unit,minimum_outcome_gap=min_outcome)
sheet.convert('RGB').save(OUT/'point_layout_before_after.png')
(W/'instruction_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
(W/'instruction_changes.json').write_text(json.dumps(changes,indent=2),encoding='utf8')
shutil.copyfile(BASE,TARGET)
with TARGET.open('r+b') as f:
    for lo,hi in ranges:f.seek(dol_at+lo);f.write(after[lo:hi])
with TARGET.open('rb') as f:f.seek(dol_at);assert f.read(len(after))==after
f,fst,fs=current_files(BASE);g,got,gs=current_files(TARGET)
assert got==fst and gs==fs and len(fs)==719
for path,(at,n,i) in fs.items():
    f.seek(at);g.seek(at);assert f.read(n)==g.read(n),path
f.close();g.close()
allowed=[(dol_at+lo,dol_at+hi) for lo,hi in ranges]
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
print('All719 resources/FST exact v58; whole-disc difference confined to one 31-word half-result coordinate block.',flush=True)
target_sha=sha(TARGET)
patch_result=make(SOURCE,TARGET,OUT/'Hikaru_no_Go_3_English_PointLayout_Test_v59.bps',dict(game='Hikaru no Go 3',version='internal test v59',base='original Japanese GHTJA4'))
assert sha(BASE)==BASE_SHA and sha(SOURCE)==SOURCE_SHA
report=dict(version='internal test v59',source_sha256=SOURCE_SHA,previous_sha256=BASE_SHA,output_sha256=target_sha,
            dol_offset=dol_at,instruction_changes=changes,checks=checks,patch=patch_result,
            all719_resources_fst_art_fonts_scripts_exact_v58=True,
            scoring_komi_winner_calculations_and_all_other_unrecorded_bytes_exact_v58=True,
            whole_disc_comparison_passed=True,original_and_v58_preserved=True,
            status='Local result-display-only test. No Dolphin runtime certification. GitHub remains1.0.1.')
(OUT/'build_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
(OUT/'README.md').write_text('''# Half-point result formatting test v59

Based on v58, which the user reports appears to work but is not fully certified.
Only one existing 31-word PowerPC block in the half-point arm of the
results-screen display routine change. It moves the .5 sprite immediately after
the integer digits, then pt, then Win/Loss: e.g. 6.5 pt Win.

No branch, hook, function call, extra code section, memory allocation, string,
font, artwork, save, scoring rule, komi or winner calculation changes. Integer
results take the untouched arm. Time-out, resignation, draw/jigo use separate
display functions. All 719 resource files, FST and all other ISO bytes are exact
v58. Earlier v58 artwork spacing improvements are retained.

The four direct callers of the routine are results-screen branches. Offline
interpretation of actual original/patched PPC words passed 8,000 combinations:
both colours/outcomes, whole and half-point margins 0..999. Integer display
writes match byte-for-byte; only three half-result X positions differ. Y,
visibility, dimensions, nonvolatile registers and stack base are preserved.
Tests include deliberately stale incoming half/outcome Y coordinates, which the
final block explicitly resets to the already-established unit Y position.
Writes are restricted to temporary stack and existing display widget fields;
numeric result state and global/save memory are not written by this block.
This is a static instruction harness with original pre-positioned widget state,
not full-game emulation or a guarantee of every runtime state.

Cold boot; verify 0.5/6.5/11.5-point results if reachable; both sides and Win/Loss;
an integer margin; resignation; draw; result exit and following dialogue/menu.
Keep v58 as fallback. GitHub has not been updated with this test.
''',encoding='utf8')
print('Built',TARGET,target_sha,flush=True)
