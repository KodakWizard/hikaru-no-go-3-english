"""One existing 31-word block: half-point result display coordinates only.

No hooks, calls, branches, allocated code, numeric-score calculations, fonts,
global constants or strings change. Original display routine 8012e8b8.
"""
from pathlib import Path
import struct,sys,re,json,random,math
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'translation_work/python_libs'))
from capstone import Cs,CS_ARCH_PPC,CS_MODE_32,CS_MODE_BIG_ENDIAN
MD=Cs(CS_ARCH_PPC,CS_MODE_32|CS_MODE_BIG_ENDIAN)
START=0x8012f04c;STOP=0x8012f120
def D(op,t,a,imm):return op<<26|t<<21|a<<16|(imm&65535)
def A(xo,t,a,c,b):return 59<<26|t<<21|a<<16|b<<11|c<<6|xo<<1
WORDS=[
 D(15,3,0,0x4330),                 # lis r3,0x4330
 D(14,0,31,-14),                   # .5 left edge = end-14
 D(36,3,1,0xd0),D(36,0,1,0xd4),   # exact integer-to-double conversion
 D(50,0,1,0xd0),D(50,3,2,-0x4200),
 A(20,0,0,0,3),                    # fsubs f0,f0,f3
 D(48,4,2,-0x4240),                # f4=0.5 (original read-only constant)
 D(32,4,28,0x48),D(14,5,0,0),D(38,5,4,0x34),
 D(48,1,4,8),A(29,0,1,4,0),D(52,0,4,0), # .5 X center
 D(14,0,31,55),D(36,0,1,0xd4),D(50,0,1,0xd0),A(20,0,0,0,3),
 D(48,1,4,12),A(30,5,1,4,0),       # pt center = end+55 - 42/2
 D(32,6,28,0x44),D(52,5,6,0),      # unit X center
 D(48,6,6,4),D(52,6,4,4),          # .5 Y = existing unit Y, explicitly set
 D(32,3,28,0x58),D(48,1,3,8),
 A(29,0,1,4,0),D(52,0,3,0),        # Win/Loss X center
 D(52,6,3,4),                      # Win/Loss Y = unit Y, explicitly set
 0x60000000,0x60000000,
]
assert len(WORDS)==31
PATCH={0x8012f054+4*i:w for i,w in enumerate(WORDS)}
EXPECTED_MNEMONICS=['lis','addi','stw','stw','lfd','lfd','fsubs','lfs','lwz','li','stb',
 'lfs','fmadds','stfs','addi','stw','lfd','fsubs','lfs','fnmsubs','lwz','stfs','lfs','stfs',
 'lwz','lfs','fmadds','stfs','stfs','nop','nop']

def sections(dol):
    return [(i,struct.unpack_from('>I',dol,i*4)[0],
             struct.unpack_from('>I',dol,0x48+i*4)[0],
             struct.unpack_from('>I',dol,0x90+i*4)[0]) for i in range(18)
            if struct.unpack_from('>I',dol,0x90+i*4)[0]]

def offset(dol,ram):
    return next(o+ram-a for _,o,a,n in sections(dol) if a<=ram<a+n)

def patch(dol):
    original=(R/'translation_work/main.dol').read_bytes()
    result=bytearray(dol);changes=[]
    for ram,word in PATCH.items():
        at=offset(dol,ram);orig_at=offset(original,ram)
        assert dol[at:at+4]==original[orig_at:orig_at+4],hex(ram)
        new=word.to_bytes(4,'big');decoded=list(MD.disasm(new,ram));assert len(decoded)==1
        assert decoded[0].mnemonic==EXPECTED_MNEMONICS[(ram-0x8012f054)//4]
        old=list(MD.disasm(dol[at:at+4],ram))[0]
        result[at:at+4]=new
        changes.append(dict(ram=hex(ram),dol_offset=hex(at),before=dol[at:at+4].hex(),
                            after=new.hex(),before_asm=old.mnemonic+' '+old.op_str,
                            after_asm=decoded[0].mnemonic+' '+decoded[0].op_str))
    return bytes(result),changes

def execute(dol,end,half,seed=0):
    """Interpret actual PPC words in the edited block and untouched integer arm.

    Starts after original score conversion/side/result selection, with their
    established sprite state. This is an offline instruction test, not Dolphin.
    Reject unmapped reads and unexpected instructions, and capture every write.
    """
    rng=random.Random(seed)
    regs=[rng.randrange(0,2**32) for _ in range(32)]
    fp=[rng.uniform(-1000,1000) for _ in range(32)]
    regs[1]=0x100000;regs[2]=0x8041b2e0;regs[28]=0x200000;regs[29]=half;regs[31]=end
    initial=regs.copy();initial_fp=fp.copy();mem={};writes=[];touched=[];cr=(False,False,False)
    def put(addr,data,record=False):
        for j,v in enumerate(data):mem[addr+j]=v
        if record:writes.append((addr,bytes(data)))
    def get(addr,n):
        assert all(addr+i in mem for i in range(n)),('unmapped',hex(addr),n)
        return bytes(mem[addr+i] for i in range(n))
    def u32(addr):return int.from_bytes(get(addr,4),'big')
    def fl(addr):return struct.unpack('>f',get(addr,4))[0]
    def s32(x):return x if x<2**31 else x-2**32
    def single(x):return struct.unpack('>f',struct.pack('>f',x))[0]
    def ea(arg):
        m=re.fullmatch(r'(-?(?:0x[0-9a-f]+|\d+))\((r\d+)\)',arg);assert m,arg
        return (regs[int(m[2][1:])]+int(m[1],0))&0xffffffff
    # Original .44 unit/.48 half/.58 outcome sprites; exact native dimensions.
    objects={0x44:0x210000,0x48:0x220000,0x58:0x230000}
    for field,addr in objects.items():
        put(regs[28]+field,struct.pack('>I',addr))
        width=68 if field==0x58 else 38
        x=end+19 if field==0x44 else -123
        # Only the unit Y is established on every incoming nonzero-score path.
        # Half/outcome Y are deliberately stale to catch reliance on old state.
        y=391 if field==0x44 else rng.uniform(-2000,2000)
        put(addr,struct.pack('>ffff',x,y,width,42))
        put(addr+0x34,b'\x01' if field==0x48 else b'\x00')
    # Load only the real read-only constants used by the block.
    for rel,n in [(-0x4200,8),(-0x4240,4),(-0x4134,4)]:
        addr=regs[2]+rel;at=offset(dol,addr);put(addr,dol[at:at+n])
    ops={i.address:(i.mnemonic,i.op_str) for i in MD.disasm(dol[offset(dol,START):offset(dol,STOP)],START)}
    pc=START
    for step in range(200):
        if pc==STOP:break
        touched.append(pc);op,operands=ops[pc];args=[x.strip() for x in operands.split(',')] if operands else []
        nxt=pc+4
        ri=lambda x:int(x[1:]);fi=ri
        if op=='nop':pass
        elif op=='li':regs[ri(args[0])]=int(args[1],0)&0xffffffff
        elif op=='lis':regs[ri(args[0])]=(int(args[1],0)<<16)&0xffffffff
        elif op=='addi':regs[ri(args[0])]=(regs[ri(args[1])]+int(args[2],0))&0xffffffff
        elif op in ('lwz','lfs','lfd'):
            addr=ea(args[1])
            if op=='lwz':regs[ri(args[0])]=u32(addr)
            else:fp[fi(args[0])]=struct.unpack('>f' if op=='lfs' else '>d',get(addr,4 if op=='lfs' else 8))[0]
        elif op in ('stw','stb','stfs'):
            addr=ea(args[1])
            if op=='stfs':raw=struct.pack('>f',fp[fi(args[0])])
            elif op=='stw':raw=struct.pack('>I',regs[ri(args[0])])
            else:raw=bytes([regs[ri(args[0])]&255])
            put(addr,raw,True)
        elif op=='fsubs':fp[fi(args[0])]=single(fp[fi(args[1])]-fp[fi(args[2])])
        elif op in ('fmadds','fnmsubs'):
            # All exercised operands are exactly representable small integers
            # or halves, so fused/non-fused host rounding yields identical bits.
            a,c,b=[fp[fi(x)] for x in args[1:]]
            fp[fi(args[0])]=single(a*c+b if op=='fmadds' else b-a*c)
        elif op=='clrlwi.':
            value=regs[ri(args[1])]&((1<<(32-int(args[2],0)))-1)
            regs[ri(args[0])]=value;cr=(s32(value)<0,s32(value)>0,value==0)
        elif op=='beq':
            if cr[2]:nxt=int(args[0],0)
        elif op=='b':nxt=int(args[0],0)
        else:raise AssertionError((hex(pc),op,operands))
        pc=nxt
    else:raise AssertionError('instruction budget')
    assert pc==STOP
    for index in [1,2,13,*range(14,32)]:assert regs[index]==initial[index],index
    for index in range(14,32):assert fp[index]==initial_fp[index],index
    # No write may reach result model, score fields, saves or globals.
    for addr,raw in writes:
        if initial[1]<=addr<initial[1]+0x130:continue
        allowed=[(o,o+8) for o in objects.values()]+[(o+0x34,o+0x35) for o in objects.values()]
        assert any(lo<=addr and addr+len(raw)<=hi for lo,hi in allowed),(hex(addr),raw)
    state={hex(field):dict(x=fl(addr),y=fl(addr+4),width=fl(addr+8),height=fl(addr+12),hidden=get(addr+0x34,1)[0])
           for field,addr in objects.items()}
    return state,writes,touched

def validate(before,after):
    counts=dict(integer_cases=0,half_cases=0,display_cases=0)
    half_addresses=set(PATCH)
    for margin in range(1000):
        end=103+38+29*(len(str(margin))-1)
        for colour in (0,1):
            for outcome in (0,1):
                for half in (0,1):
                    seed=margin*8+colour*4+outcome*2+half
                    old,ow,ot=execute(before,end,half,seed)
                    new,nw,nt=execute(after,end,half,seed)
                    assert ot==nt
                    if not half:
                        assert old==new and ow==nw and not set(nt)&half_addresses
                        counts['integer_cases']+=1
                    else:
                        assert new['0x48']['x']-19==end-14
                        assert new['0x44']['x']-19==end+15
                        assert new['0x58']['x']-34==end+55
                        assert old['0x44']['x']-19==end
                        assert old['0x48']['x']-19==end+38
                        assert old['0x58']['x']==end+110
                        for field in old:
                            for key in ('y','width','height','hidden'):assert old[field][key]==new[field][key]
                        assert new['0x48']['y']==new['0x58']['y']==391
                        counts['half_cases']+=1
                    counts['display_cases']+=1
    # Additional exact-integer placement extremes beyond ordinary board scores.
    for end in [0,103,141,170,199,1000,65535]:
        for half in (0,1):execute(after,end,half,seed=89+end)
    return counts|dict(actual_ppc_words_interpreted=True,integer_path_and_writes_exact=True,
                       half_changes_only_three_x_coordinates=True,
                       stale_incoming_half_and_outcome_y_tested=True,
                       y_visibility_dimensions_and_nonvolatile_registers_preserved=True,
                       score_data_global_constants_and_save_memory_not_written=True,
                       limits='Offline block execution with original pre-positioned sprite state; not Dolphin gameplay.')

if __name__=='__main__':
    with (R/'English_ResultSpacing_Test_v58/Hikaru no Go 3 - English Result Spacing Test v58.iso').open('rb') as f:
        f.seek(0x420);at=int.from_bytes(f.read(4),'big');f.seek(at);header=f.read(0x100)
        n=max(o+s for _,o,a,s in sections(header));f.seek(at);dol=f.read(n)
    new,changes=patch(dol);print(json.dumps(changes,indent=2));print(validate(dol,new))
