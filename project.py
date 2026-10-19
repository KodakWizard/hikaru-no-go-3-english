"""Portable Version 1 patch application and conservative English text editing.

Python 3.10+, standard library only. Never opens memory-card or emulator files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import zlib

SOURCE_SHA = 'c6882110afa9ef27bf49f2e0530e37c51164d5ad0c10466cb164fc1b938406fc'
TARGET_SHA = 'fe7839ca19d0fe4fedf21f552dfc742f092e28ca052342979474004b3e58ca6d'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def require(condition,message):
    if not condition:raise ValueError(message)

def patch_commands(patch,source_size):
    require(patch[:4]==b'BPS1','Not a BPS1 patch')
    require(len(patch)>=16,'Truncated patch')
    require(zlib.crc32(patch[:-4])==int.from_bytes(patch[-4:],'little'),'Patch checksum mismatch')
    pos=4
    def number():
        nonlocal pos
        value=0;shift=1
        for _ in range(10):
            require(pos<len(patch)-12,'Truncated BPS command')
            x=patch[pos];pos+=1;value+=(x&127)*shift
            if x&128:return value
            shift<<=7;value+=shift
        raise ValueError('Oversized BPS integer')
    ss,ts,ms=number(),number(),number()
    require(ss==source_size and ts==source_size,'Unexpected image size')
    pos+=ms;require(pos<=len(patch)-12,'Invalid metadata length')
    produced=0
    while produced<ts:
        command=number();n=(command>>2)+1;action=command&3
        require(action in (0,1),'Only this project’s SourceRead/TargetRead BPS variant is supported')
        require(produced+n<=ts,'BPS output exceeds declared size')
        if action==1:
            require(pos+n<=len(patch)-12,'Truncated literal')
            yield produced,n,patch[pos:pos+n];pos+=n
        else:yield produced,n,None
        produced+=n
    require(pos==len(patch)-12,'Unexpected trailing BPS commands')

def apply(source,patch_path,output):
    require(sha(source)==SOURCE_SHA,'Wrong source. Supply the unmodified Japanese GHTJA4 ISO matching README SHA-256.')
    patch=Path(patch_path).read_bytes()
    # Fully validate commands before creating an output.
    for _ in patch_commands(patch,Path(source).stat().st_size):pass
    crc=0
    try:
        with Path(output).open('xb') as out,Path(source).open('rb') as src:
            for at,n,literal in patch_commands(patch,Path(source).stat().st_size):
                if literal is not None:out.write(literal);crc=zlib.crc32(literal,crc)
                else:
                    src.seek(at)
                    while n:
                        data=src.read(min(n,8*1024*1024));require(bool(data),'Truncated source')
                        out.write(data);crc=zlib.crc32(data,crc);n-=len(data)
        require(crc==int.from_bytes(patch[-8:-4],'little'),'Output CRC mismatch')
        require(sha(output)==TARGET_SHA,'Output SHA-256 mismatch; do not use this image')
    except Exception:
        # Keep a failed output for diagnosis. The caller never overwrites a file.
        raise
    print('Verified Version 1 beta:',output)

def file_locations(f):
    f.seek(0x420);dol,at,n=struct.unpack('>III',f.read(12))
    f.seek(at);fst=f.read(n);count=int.from_bytes(fst[8:12],'big');names=fst[count*12:]
    files={};stack=[('',count)]
    for i in range(1,count):
        while i>=stack[-1][1]:stack.pop()
        a,b,c=struct.unpack_from('>III',fst,i*12);p=a&0xffffff
        name=names[p:names.index(0,p)].decode('ascii');path=stack[-1][0]+name
        if a>>24:stack.append((path+'/',c))
        else:files[path]=(b,c)
    return dol,files

def edit(source,catalog_path,output):
    require(sha(source)==TARGET_SHA,'Text edits must start from the exact Version 1 beta image')
    catalog=json.loads(Path(catalog_path).read_text(encoding='utf8'));edits={}
    token=lambda s:re.findall(r'\$[0-9]|%[-0-9]*[sd]',s)
    with Path(source).open('rb') as f:
        dol,files=file_locations(f)
        for row in catalog:
            before=row['baseline'];after=row['english'];raw=after.encode('cp932')
            require('\0' not in after and '\r' not in after,'Embedded null/CR: '+row['id'])
            require(token(before)==token(after),'Changed placeholders: '+row['id'])
            require(len(raw)<=row['capacity_bytes'],'Text exceeds fixed byte capacity: '+row['id'])
            if row['area']=='dol':at=dol+row['offset']
            else:
                off,size=files[row['path']]
                require(row['offset']+row['capacity_bytes']+1<=size,'Script boundary exceeded')
                at=off+row['offset']
            f.seek(at);require(f.read(len(before.encode('cp932'))+1)==before.encode('cp932')+b'\0','Baseline mismatch: '+row['id'])
            budget=row.get('line_budget')
            if budget:
                sep=row['line_break'];lines=after.split(sep)
                cells=lambda s:len(re.sub(r'\$[0-9]','X'*12,s).encode('cp932'))
                require(len(lines)<=budget[1] and max(map(cells,lines))<=budget[0],'Line budget exceeded: '+row['id'])
            if before==after:continue
            if at in edits:require(edits[at]==raw,'Conflicting shared string edits')
            edits[at]=raw
    spans=sorted((at,at+len(raw)+1) for at,raw in edits.items())
    require(all(x[1]<=y[0] for x,y in zip(spans,spans[1:])),'Overlapping edits')
    with Path(source).open('rb') as src,Path(output).open('xb') as out:
        shutil.copyfileobj(src,out,8*1024*1024)
        for at,raw in edits.items():out.seek(at);out.write(raw+b'\0')
    print(f'Wrote {len(edits)} text slots; SHA-256 {sha(output)}')
    print('Community build: gameplay and visual checks required; original beta checksum no longer applies.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('apply');p.add_argument('source');p.add_argument('patch');p.add_argument('output')
    p=sub.add_parser('edit');p.add_argument('source');p.add_argument('catalog');p.add_argument('output')
    p=sub.add_parser('hash');p.add_argument('file')
    args=parser.parse_args()
    if args.command=='apply':apply(args.source,args.patch,args.output)
    elif args.command=='edit':edit(args.source,args.catalog,args.output)
    else:print(sha(args.file))

if __name__=='__main__':main()
