"""Read-only release audit and export of current editable, verified text slots."""
from pathlib import Path
import hashlib, json, re, struct
from gcs_text import text_tail
from gba_lz_v34 import decode as lzdecode
from decode_bpe import decode
from textures import resources, texture

ROOT = Path(__file__).resolve().parent
TARGET = ROOT/'English_PointLayout_Test_v59/Hikaru no Go 3 - English Point Layout Test v59.iso'
ORIGINAL = ROOT/'Hikaru no Go 3 (Japan).iso'
OUT = ROOT/'translation_work/release_qa_v102'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024), b''):h.update(b)
    return h.hexdigest()

class Disc:
    def __init__(self,path):
        self.f=path.open('rb');self.size=path.stat().st_size
        h=self.read(0,0x440)
        self.dol_at,self.fst_at,self.fst_size=struct.unpack_from('>III',h,0x420)
        fst=self.read(self.fst_at,self.fst_size)
        count=int.from_bytes(fst[8:12],'big');names=fst[count*12:]
        self.files={};stack=[('',count)]
        for i in range(1,count):
            while i>=stack[-1][1]:stack.pop()
            a,b,c=struct.unpack_from('>III',fst,i*12)
            no=a&0xffffff;name=names[no:names.index(0,no)].decode('ascii')
            path=stack[-1][0]+name
            if a>>24:stack.append((path+'/',c))
            else:
                assert path not in self.files and 0<=b<=b+c<=self.size
                self.files[path]=(b,c)
        header=self.read(self.dol_at,0x100)
        self.sections=[]
        for i in range(18):
            off=struct.unpack_from('>I',header,i*4)[0]
            ram=struct.unpack_from('>I',header,0x48+i*4)[0]
            size=struct.unpack_from('>I',header,0x90+i*4)[0]
            if size:self.sections.append((i,off,ram,size))
        self.dol=self.read(self.dol_at,max(o+n for _,o,_,n in self.sections))
    def read(self,off,n):
        self.f.seek(off);b=self.f.read(n);assert len(b)==n;return b
    def file(self,path):return self.read(*self.files[path])
    def close(self):self.f.close()

def string(data,at):
    assert 0<=at<len(data)
    return data[at:data.index(0,at)].decode('cp932')

def main():
    OUT.mkdir(exist_ok=True)
    expected=json.loads((TARGET.parent/'build_report.json').read_text())
    assert sha(ORIGINAL)==expected['source_sha256']
    assert sha(TARGET)==expected['output_sha256']
    a,b=Disc(ORIGINAL),Disc(TARGET)
    report={'version':'1.0.2-beta','source_sha256':expected['source_sha256'],
            'target_sha256':expected['output_sha256'],'active_files':len(b.files),
            'runtime_status':'PENDING manual checklist; not full-game certification',
            'checks':{},'coverage_gaps':[], 'residual_candidates':[]}
    assert set(a.files)==set(b.files) and len(b.files)==719
    intervals=sorted((o,o+n,p) for p,(o,n) in b.files.items() if n)
    for x,y in zip(intervals,intervals[1:]):assert x[1]<=y[0],(x,y)
    for lo,hi,p in intervals:
        assert not (lo<b.dol_at+len(b.dol) and b.dol_at<hi),p
        assert not (lo<b.fst_at+b.fst_size and b.fst_at<hi),p
    report['checks']['fst_and_dol_extents']='PASS'
    prior=json.loads((ROOT/'English_NameEntry_Test_v55/build_report.json').read_text())
    changes={int(k,16):int(v,16) for k,v in prior['code_edits'].items()}
    from point_layout_v59 import PATCH
    assert len(PATCH)==31 and not (set(PATCH)&set(changes))
    changes.update(PATCH)
    checked=set()
    for i,off,ram,n in a.sections:
        if i>=7:continue
        assert next(x for x in b.sections if x[0]==i)==(i,off,ram,n)
        for p in range(off,off+n,4):
            address=ram+p-off;now=b.dol[p:p+4];old=a.dol[p:p+4]
            if address in changes:
                assert now==changes[address].to_bytes(4,'big');checked.add(address)
            else:assert now==old,hex(address)
    assert checked==set(changes)
    from name_entry_v55 import code, validate
    generated=code()
    # code() returns bytes and label addresses.
    blob=generated[0] if isinstance(generated,tuple) else generated
    section=next(s for s in b.sections if s[0]==2)
    assert b.dol[section[1]:section[1]+section[3]]==blob
    report['checks']['name_entry_offline']=validate()
    report['checks']['executable_whitelist']='PASS: 12 documented v55 sites, declared helper section and exact final v59 31-word display window'
    catalog=[];japanese=re.compile('[\u3040-\u30ff\u4e00-\u9fff]')
    tokens=lambda s:re.findall(r'\$[0-9]|%[sd]',re.sub(r'%[-0-9]+([sd])',r'%\1',s))
    rows=json.loads((ROOT/'translation_work/qa_v52/current_corpus.json').read_text(encoding='utf8'))
    dolrows=[r for r in rows if r['area']=='dol'];battle=0;large=0
    for r in dolrows:
        p=int(r['location'],16);text=string(b.dol,p)
        assert tokens(text)==tokens(r['japanese']),(r['location'],text)
        if 0x259214<=p<=0x260178:
            assert len(text.split('↓'))<=3 and max(len(s.encode('cp932')) for s in text.split('↓'))<=18,(hex(p),text)
            battle+=1
        elif p>=0x26020c or 0x258ec0<=p<=0x258fe0:
            if p<=0x275950:
                cells=lambda s:len(re.sub(r'\$[0-9]','X'*12,s).encode('cp932'))
                assert len(text.split('↓'))<=3 and max(map(cells,text.split('↓')))<=26,(hex(p),text)
                large+=1
        catalog.append(dict(id='dol:'+hex(p),area='dol',offset=p,english=text,japanese=r['japanese'],capacity_bytes=len(text.encode('cp932'))))
        if japanese.search(text):report['residual_candidates'].append({'area':'dol','location':hex(p),'text':text})
    report['checks']['dol_entries']=len(dolrows)
    report['checks']['small_bubble_budget']=battle
    report['checks']['large_bubble_budget']=large
    count=0;parsed=0
    for path in sorted(b.files):
        if not path.endswith('.gcs'):continue
        original,current=a.file(path),b.file(path)
        try:base,start,rr=text_tail(original)
        except ValueError:
            report['coverage_gaps'].append('Unsupported complete dispatcher parser: '+path);continue
        # Some dispatchers store directly referenced feedback before their A6
        # heading pool. Validate those operands rather than calling them code.
        early={}
        for q in range(base+4,start,4):
            if int.from_bytes(original[q-4:q],'big') not in (0x87,0xa6,0x103):continue
            p=base+int.from_bytes(original[q:q+4],'big')
            if not q+4<=p<start:continue
            try:text=string(original,p)
            except (ValueError,UnicodeDecodeError):continue
            if not japanese.search(text):continue
            early.setdefault(p,dict(offset=p,japanese=text,references=[]))['references'].append(q)
        rr=list(early.values())+rr
        start=min([start]+list(early))
        parsed+=1;ptrs=set()
        for index,r in enumerate(rr):
            refs=[p for p in r['references'] if int.from_bytes(original[p-4:p],'big') in (0x87,0xa6,0x103)]
            if not refs:continue
            texts=[string(current,base+int.from_bytes(current[p:p+4],'big')) for p in refs]
            assert len(set(texts))==1 and tokens(texts[0])==tokens(r['japanese']),(path,index)
            ptrs.update(q for p in refs for q in range(p,p+4));count+=1
            p=base+int.from_bytes(current[refs[0]:refs[0]+4],'big')
            catalog.append(dict(id=f'{path}:{index}',area='script',path=path,offset=p,english=texts[0],japanese=r['japanese'],capacity_bytes=len(texts[0].encode('cp932'))))
            if japanese.search(texts[0]):report['residual_candidates'].append({'area':'script','path':path,'text':texts[0]})
        prefix_diffs=[p for p in range(start) if p not in ptrs and current[p]!=original[p]]
        assert not prefix_diffs,(path,[(hex(p),original[p:p+4].hex(),current[p:p+4].hex()) for p in prefix_diffs[:16]])
    report['checks']['parsed_scripts']=parsed;report['checks']['script_entries_and_operands']=count
    def read(path):return b.file(path)
    common=b''.join(lzdecode(read(f'gba/dacs/tutocmn/tutorial1_dacs_0_{i}_LZ.bin')) for i in range(40))
    match=b''.join(lzdecode(read(f'gba/dacs/magnet/btlmenu_dacs_{i}_LZ.bin')) if i<40 else read(f'gba/dacs/magnet/btlmenu_dacs_{i}.bin') for i in range(45))
    matchrows=[r for r in rows if r['area']=='gba_match']
    for r in matchrows:
        text=string(match,int(r['location'],16))
        assert tokens(text)==tokens(r['japanese'])
        if japanese.search(text):report['residual_candidates'].append({'area':'gba_match','location':r['location'],'text':text})
    manifest=json.loads((ROOT/'gba_books_manifest_v35.json').read_text(encoding='utf8'));books=0
    for book,rr in manifest.items():
        paths=sorted((p for p in b.files if p.startswith(f'gba/dacs/tutorial{book}_dacs/')),key=lambda p:int(p.split('_')[-2]))
        rom=common+b''.join(lzdecode(read(p)) for p in paths)
        for r in rr:
            texts=[string(rom,int.from_bytes(rom[p:p+4],'little')-0x09f00000) for p in r['references']]
            assert len(set(texts))==1 and tokens(texts[0])==tokens(r['japanese']),(book,r['offset'])
            books+=1
            if japanese.search(texts[0]):report['residual_candidates'].append({'area':'gba_book','book':book,'text':texts[0]})
    report['checks']['gba_match_entries']=len(matchrows);report['checks']['gba_book_entries']=books
    archives=images=0
    native_baseline=Disc(ROOT/'English_FontRestore_v53/Hikaru no Go 3 - English Font Restore v53.iso')
    for path in sorted(b.files):
        if not path.endswith('.bpe'):continue
        data=decode(b.file(path));original=decode(native_baseline.file(path));archives+=1
        assert len(data)==len(original),path
        rr=list(resources(data));old=dict(resources(original))
        assert [n for n,_ in rr]==[n for n,_ in resources(original)],path
        for name,p in rr:
            if not name.endswith('.D4'):continue
            im,desc=texture(data,p);oi,od=texture(original,old[name])
            assert desc[:3]==od[:3],(path,name,desc,od)
            images+=1
    report['checks']['native_archives_decoded']=archives;report['checks']['native_images_decoded']=images
    report['coverage_gaps'] += ['Manual gameplay routes, optional Story branches and actual GBA transfer pending.', 'GBA compound kanji-number formatter and packed character graphics remain unclassified.', 'Font outline clipping and all bubble variants require visual runtime comparison.', 'Japanese background building/shop signage and collectible packaging retained with approval.']
    (OUT/'editable_text.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    a.close();b.close();native_baseline.close()
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
