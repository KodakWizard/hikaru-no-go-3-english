"""Emit the PowerPC routines for compact player names."""
import struct

# Load address of the new executable section and the first byte the heap can use.
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
 # System startup: raise the heap start past the name routines if necessary.
 a.label('arena_floor')
 a.d(15,0,0,RESERVED_END>>16);a.d(24,0,0,RESERVED_END&65535)
 # cmplw r3,r0, CR0. Preserve LR, stack, and all nonvolatile registers.
 a.op(0x7c030040);a.b('ge','arena_store');a.op(0x7c030378) # mr r3,r0
 a.label('arena_store');a.d(36,3,13,-0x6fb8);a.op(0x4e800020)
 # Confirm a name: read full-width Latin letters and digits as two bytes,
 # then write the corresponding one-byte ASCII character to the saved-name buffer.
 # r3 is the destination, r4 is the source, and r5 tracks the write position.
 a.label('narrow')
 a.add(5,3,0)
 a.label('n_loop');a.load(6,4);a.cmp(6,0);a.b('eq','n_end');a.cmp(6,0x82);a.b('ne','n_copy')
 a.load(7,4,1);a.cmp(7,0x4f);a.b('lt','n_copy');a.cmp(7,0x58);a.b('le','n_minus31')
 a.cmp(7,0x60);a.b('lt','n_copy');a.cmp(7,0x79);a.b('le','n_minus31')
 a.cmp(7,0x81);a.b('lt','n_copy');a.cmp(7,0x9a);a.b('gt','n_copy')
 a.add(6,7,-0x20);a.b('b','n_emit')
 a.label('n_minus31');a.add(6,7,-0x1f)
 a.label('n_emit');a.add(4,4,2);a.save(6,5);a.add(5,5,1);a.b('b','n_loop')
 # Copy other Shift-JIS characters as a unit, including their second byte.
 a.label('n_copy');a.save(6,5);a.add(4,4,1);a.add(5,5,1)
 a.cmp(6,0x81);a.b('lt','n_loop');a.cmp(6,0x9f);a.b('le','n_trail')
 a.cmp(6,0xe0);a.b('lt','n_loop');a.cmp(6,0xfc);a.b('gt','n_loop')
 a.label('n_trail');a.load(6,4);a.cmp(6,0);a.b('eq','n_end');a.save(6,5);a.add(4,4,1);a.add(5,5,1);a.b('b','n_loop')
 a.label('n_end');a.save(6,5);a.op(0x4e800020)
 # Reopen the editor: expand ASCII letters and digits to two-byte slots.
 # r8 counts the remaining payload bytes. The 11th byte is for the terminator.
 a.label('expand')
 a.add(5,3,0);a.li(8,10)
 a.label('e_loop');a.cmp(8,0);a.b('eq','e_end');a.load(6,4);a.cmp(6,0);a.b('eq','e_end')
 a.cmp(6,0x30);a.b('lt','e_copy');a.cmp(6,0x39);a.b('le','e_plus31')
 a.cmp(6,0x41);a.b('lt','e_copy');a.cmp(6,0x5a);a.b('le','e_plus31')
 a.cmp(6,0x61);a.b('lt','e_copy');a.cmp(6,0x7a);a.b('gt','e_copy')
 a.add(7,6,0x20);a.b('b','e_emit')
 a.label('e_plus31');a.add(7,6,0x1f)
 a.label('e_emit');a.cmp(8,2);a.b('lt','e_end');a.li(6,0x82);a.save(6,5);a.save(7,5,1);a.add(5,5,2);a.add(4,4,1);a.add(8,8,-2);a.b('b','e_loop')
 # Copy other characters in their existing encoding.
 a.label('e_copy');a.save(6,5);a.add(4,4,1);a.add(5,5,1);a.add(8,8,-1)
 a.cmp(6,0x81);a.b('lt','e_loop');a.cmp(6,0x9f);a.b('le','e_trail')
 a.cmp(6,0xe0);a.b('lt','e_loop');a.cmp(6,0xfc);a.b('gt','e_loop')
 a.label('e_trail');a.cmp(8,0);a.b('eq','e_end');a.load(6,4);a.cmp(6,0);a.b('eq','e_end');a.save(6,5);a.add(4,4,1);a.add(5,5,1);a.add(8,8,-1);a.b('b','e_loop')
 a.label('e_end');a.li(6,0);a.save(6,5);a.op(0x4e800020)
 blob=a.finish();assert CODE_BASE+len(blob)<=RESERVED_END
 return blob,a.labels
