"""Scoped CNameInput conversion, with a declared section and reserved arena memory."""
import struct, random, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'translation_work/python_libs'))
from capstone import Cs,CS_ARCH_PPC,CS_MODE_32,CS_MODE_BIG_ENDIAN
CODE_BASE=0x8042c000
RESERVED_END=0x8042c400

def branch(src,dst,link=False):
 delta=dst-src
 assert delta%4==0 and -(1<<25)<=delta<(1<<25)
 return 0x48000000|(delta&0x3fffffc)|int(link)

class Asm:
 def __init__(self,base): self.base=base;self.nodes=[];self.labels={}
 def label(self,n): self.labels[n]=self.base+len(self.nodes)*4
 def op(self,w):self.nodes.append(w)
 def d(self,op,rt,ra,imm):self.op(op<<26|rt<<21|ra<<16|(imm&65535))
 def li(self,r,v):self.d(14,r,0,v)
 def add(self,t,a,v):self.d(14,t,a,v)
 def load(self,t,a,v=0):self.d(34,t,a,v)
 def save(self,t,a,v=0):self.d(38,t,a,v)
 def cmp(self,r,v):self.d(11,0,r,v)
 def b(self,kind,label):self.nodes.append((kind,label))
 def finish(self):
  out=[];conds={'eq':(12,2),'ne':(4,2),'lt':(12,0),'le':(4,1),'gt':(12,1),'ge':(4,0)}
  for i,w in enumerate(self.nodes):
   if isinstance(w,tuple):
    kind,l=w;at=self.base+i*4;dst=self.labels[l]
    if kind=='b':w=branch(at,dst)
    else:
     bo,bi=conds[kind];delta=dst-at;assert -32768<=delta<32768
     w=16<<26|bo<<21|bi<<16|(delta&0xfffc)
   out.append(w)
  return b''.join(struct.pack('>I',x) for x in out)

def code():
 a=Asm(CODE_BASE)
 a.label('arena_floor')
 a.d(15,0,0,RESERVED_END>>16);a.d(24,0,0,RESERVED_END&65535)
 # cmplw r3,r0, CR0. Preserve LR, stack, and all nonvolatile registers.
 a.op(0x7c030040);a.b('ge','arena_store');a.op(0x7c030378) # mr r3,r0
 a.label('arena_store');a.d(36,3,13,-0x6fb8);a.op(0x4e800020)
 a.label('narrow')
 a.add(5,3,0)
 a.label('n_loop');a.load(6,4);a.cmp(6,0);a.b('eq','n_end');a.cmp(6,0x82);a.b('ne','n_copy')
 a.load(7,4,1);a.cmp(7,0x4f);a.b('lt','n_copy');a.cmp(7,0x58);a.b('le','n_minus31')
 a.cmp(7,0x60);a.b('lt','n_copy');a.cmp(7,0x79);a.b('le','n_minus31')
 a.cmp(7,0x81);a.b('lt','n_copy');a.cmp(7,0x9a);a.b('gt','n_copy')
 a.add(6,7,-0x20);a.b('b','n_emit')
 a.label('n_minus31');a.add(6,7,-0x1f)
 a.label('n_emit');a.add(4,4,2);a.save(6,5);a.add(5,5,1);a.b('b','n_loop')
 a.label('n_copy');a.save(6,5);a.add(4,4,1);a.add(5,5,1)
 a.cmp(6,0x81);a.b('lt','n_loop');a.cmp(6,0x9f);a.b('le','n_trail')
 a.cmp(6,0xe0);a.b('lt','n_loop');a.cmp(6,0xfc);a.b('gt','n_loop')
 a.label('n_trail');a.load(6,4);a.cmp(6,0);a.b('eq','n_end');a.save(6,5);a.add(4,4,1);a.add(5,5,1);a.b('b','n_loop')
 a.label('n_end');a.save(6,5);a.op(0x4e800020)
 a.label('expand')
 a.add(5,3,0);a.li(8,10)
 a.label('e_loop');a.cmp(8,0);a.b('eq','e_end');a.load(6,4);a.cmp(6,0);a.b('eq','e_end')
 a.cmp(6,0x30);a.b('lt','e_copy');a.cmp(6,0x39);a.b('le','e_plus31')
 a.cmp(6,0x41);a.b('lt','e_copy');a.cmp(6,0x5a);a.b('le','e_plus31')
 a.cmp(6,0x61);a.b('lt','e_copy');a.cmp(6,0x7a);a.b('gt','e_copy')
 a.add(7,6,0x20);a.b('b','e_emit')
 a.label('e_plus31');a.add(7,6,0x1f)
 a.label('e_emit');a.cmp(8,2);a.b('lt','e_end');a.li(6,0x82);a.save(6,5);a.save(7,5,1);a.add(5,5,2);a.add(4,4,1);a.add(8,8,-2);a.b('b','e_loop')
 a.label('e_copy');a.save(6,5);a.add(4,4,1);a.add(5,5,1);a.add(8,8,-1)
 a.cmp(6,0x81);a.b('lt','e_loop');a.cmp(6,0x9f);a.b('le','e_trail')
 a.cmp(6,0xe0);a.b('lt','e_loop');a.cmp(6,0xfc);a.b('gt','e_loop')
 a.label('e_trail');a.cmp(8,0);a.b('eq','e_end');a.load(6,4);a.cmp(6,0);a.b('eq','e_end');a.save(6,5);a.add(4,4,1);a.add(5,5,1);a.add(8,8,-1);a.b('b','e_loop')
 a.label('e_end');a.li(6,0);a.save(6,5);a.op(0x4e800020)
 blob=a.finish();assert CODE_BASE+len(blob)<=RESERVED_END
 return blob,a.labels

def execute(blob,entry,raw=None,arena=None):
 md=Cs(CS_ARCH_PPC,CS_MODE_32|CS_MODE_BIG_ENDIAN)
 ops={i.address:(i.mnemonic,i.op_str) for i in md.disasm(blob,CODE_BASE)}
 regs={f'r{i}':0x110000+i*0x100 for i in range(32)};initial=regs.copy()
 regs['r3']=0x200000 if arena is None else arena;regs['r4']=0x100000;regs['r13']=0x300000
 initial.update({k:regs[k] for k in ['r1','r13']})
 mem={} if raw is None else {0x100000+i:v for i,v in enumerate(raw+b'\0')}
 writes=[];pc=entry;cr=(False,False,False)
 import re
 for step in range(10000):
  op,s=ops[pc];args=[v.strip() for v in s.split(',')];nxt=pc+4
  if op=='li':regs[args[0]]=int(args[1],0)&0xffffffff
  elif op=='lis':regs[args[0]]=(int(args[1],0)<<16)&0xffffffff
  elif op=='ori':regs[args[0]]=regs[args[1]]|int(args[2],0)
  elif op=='mr':regs[args[0]]=regs[args[1]]
  elif op=='addi':regs[args[0]]=(regs[args[1]]+int(args[2],0))&0xffffffff
  elif op in ['lbz','stb','stw']:
   m=re.fullmatch(r'(-?(?:0x[0-9a-f]+|\d+))\((r\d+)\)',args[1]);assert m
   adr=regs[m[2]]+int(m[1],0)
   if op=='lbz':assert adr in mem;regs[args[0]]=mem[adr]
   else:
    width=4 if op=='stw' else 1
    for j in range(width):
     at=adr+j;mem[at]=(regs[args[0]]>>(8*(width-j-1)))&255;writes.append(at)
  elif op in ['cmpwi','cmplw']:
   lhs=regs[args[0]];rhs=int(args[1],0) if op=='cmpwi' else regs[args[1]]
   cr=(lhs<rhs,lhs>rhs,lhs==rhs)
  elif op in ['beq','bne','blt','ble','bgt','bge','b']:
   take={'beq':cr[2],'bne':not cr[2],'blt':cr[0],'ble':not cr[1],'bgt':cr[1],'bge':not cr[0],'b':True}[op]
   if take:nxt=int(args[-1],0)
  elif op=='blr':break
  else:raise AssertionError((hex(pc),op,s))
  pc=nxt
 else:raise AssertionError('Unbounded helper')
 assert all(regs[f'r{i}']==initial[f'r{i}'] for i in [1,2,13,*range(14,32)])
 if raw is not None:
  assert regs['r3']==0x200000 and all(0x200000<=p<=0x20000a for p in writes)
  assert bytes(mem[0x100000+i] for i in range(len(raw)+1))==raw+b'\0'
  out=bytearray();p=0x200000
  while mem[p]:out.append(mem[p]);p+=1
  return bytes(out)
 assert set(writes)==set(range(0x300000-0x6fb8,0x300000-0x6fb8+4))
 assert int.from_bytes(bytes(mem[p] for p in sorted(writes)),'big')==max(arena,RESERVED_END)

def validate():
 blob,labels=code();rng=random.Random(55)
 alphabet='ＡＢＣＤＥＸＹＺａｂｃｘｙｚ０１９あいうカキ藤崎佐為！？　'
 samples=['','Ｄｏｋｉ','藤崎あかり','ＡあＢ','１２３４５','ｚＺ９！？']
 samples += [chr(c) for lo,hi in [(0xff10,0xff19),(0xff21,0xff3a),(0xff41,0xff5a)] for c in range(lo,hi+1)]
 samples += [''.join(rng.choice(alphabet) for _ in range(rng.randrange(6))) for _ in range(2000)]
 for text in samples:
  plain=''.join(chr(ord(c)-0xfee0) if '０'<=c<='９' or 'Ａ'<=c<='Ｚ' or 'ａ'<=c<='ｚ' else c for c in text)
  narrow=execute(blob,labels['narrow'],text.encode('cp932'));assert narrow==plain.encode('cp932')
  expanded=execute(blob,labels['expand'],narrow);assert expanded==text.encode('cp932')
  # Original editor's strlen/2 count and two-byte deletion remain valid.
  assert len(expanded)//2==len(text)
  if text:assert expanded[:-2].decode('cp932')==text[:-1]
  assert execute(blob,labels['narrow'],expanded)==narrow
 for val in [0x80429d98,0x8042bda0,CODE_BASE,RESERVED_END,RESERVED_END+32,0x80500000]:execute(blob,labels['arena_floor'],arena=val)
 return dict(cases=len(samples),arena_cases=6,code_bytes=len(blob),labels={k:hex(labels[k]) for k in ['arena_floor','narrow','expand']},source_unchanged=True,nonvolatile_registers_stack_preserved=True,bounded_editor_capacity_bytes=10)

if __name__=='__main__': print(validate())
