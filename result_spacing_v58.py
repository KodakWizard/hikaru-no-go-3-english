"""Move existing result glyph pixels inside their original atlas cells.

No font redraw, resampling, new stroke/halo, code edit, crop-table edit or palette
change. Native reason/result rectangles partly overlap, so ink must not occupy
the entire rectangle. Align the existing 24px source lettering to one baseline.
"""
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw, ImageChops
from textures import resources, texture
from collections import Counter
import json
R=Path(__file__).resolve().parent
W=R/'translation_work/results_v58'
GRIDS={
 'win43_0.D4':(32,38,[str(i) for i in range(10)]),
 'win43_1.D4':(32,38,['MV','']),
 'win43_2.D4':(38,42,['W','B','pt','.5']),
 'win43_3.D4':(38,42,[str(i) for i in range(10)]),
 'win43_4.D4':(68,42,['Win','Loss']),
 'win43_5.D4':(138,42,['Time','Jigo','Resign','Draw']),
}

def edits(blob):
    lookup=dict(resources(blob));out={};audit=[]
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',24*6)
    ascent=font.getmetrics()[0]
    for name,(cw,ch,labels) in GRIDS.items():
        before=texture(blob,lookup[name])[0]
        after=before.copy()
        for i,text in enumerate(labels):
            if not text:continue
            box=(i*cw,0,(i+1)*cw,ch)
            cell=before.crop(box)
            bbox=cell.getchannel('A').getbbox();assert bbox
            # v49 used a vertically centered textbbox including 1.5px edging.
            # Undo that per-word centering using the exact original font metrics.
            bounds=font.getbbox(text,stroke_width=9)
            old_baseline=((ch*6-(bounds[3]-bounds[1]))/2-bounds[1]+ascent)/6
            desired_baseline=28 if ch==38 else 30
            dy=round(desired_baseline-old_baseline)
            dx=0
            if name=='win43_5.D4':
                # Resign at x103 + centered ink reached Win at x201.
                # Keep all reason ink in the left part of its existing cell.
                dx=(6 if text in ('Time','Resign') else 11)-bbox[0]
            moved=Image.new('RGBA',cell.size,(0,0,0,0))
            ink=cell.crop(bbox)
            x,y=bbox[0]+dx,bbox[1]+dy
            assert x>=1 and y>=1 and x+ink.width<=cw-1 and y+ink.height<=ch-1,(name,text,bbox,dx,dy)
            moved.paste(ink,(x,y))
            # Every pre-existing visible RGBA pixel appears exactly once.
            visible=lambda im:Counter(p for p in im.getdata() if p[3])
            assert visible(cell)==visible(moved),(name,text,'clipped or altered ink')
            after.paste(moved,box[:2])
            audit.append(dict(image=name,label=text,cell=list(box),translation=[dx,dy],
                              before_bbox=list(bbox),after_bbox=list(moved.getchannel('A').getbbox()),
                              baseline=desired_baseline,visible_pixels_exact=True))
        out[name]=after
    return out,audit

def layout_audit(before,after):
    """Static placement model from original result-setter instructions.

    This checks decoded sprite coverage at original anchors, not gameplay.
    Original constructors: 80132660 (68x42), 80132910 (138x42).
    Setters: 8012fb94 resignation/time, 801302ec draw, 8013050c jigo,
    8012e8b8 points, 8012f140 one/two/three-digit margins.
    """
    def tile(images,atlas,i):
        cw,ch,_=GRIDS[atlas];return images[atlas].crop((i*cw,0,(i+1)*cw,ch))
    def token(images,atlas,index,x):return (tile(images,atlas,index),x,GRIDS[atlas][2][index])
    def point(images,side,margin,half,win):
        ts=[token(images,'win43_2.D4',side,65)]
        digits=str(margin)
        for i,d in enumerate(digits):ts.append(token(images,'win43_3.D4',int(d),106+29*i))
        end=103+38+29*(len(digits)-1)
        ts.append(token(images,'win43_2.D4',2,end))
        if half:ts.append(token(images,'win43_2.D4',3,end+38))
        ts.append(token(images,'win43_4.D4',win,end+(76 if half else 38)))
        return ts
    def special(images,side,reason,win):
        return [token(images,'win43_2.D4',side,65),token(images,'win43_5.D4',reason,103),
                token(images,'win43_4.D4',win,236 if reason==0 else 201)]
    def measure(ts):
        bounds=[];overlap=0
        for im,x,label in ts:
            b=im.getchannel('A').getbbox()
            bounds.append((x+b[0],x+b[2],label))
        for left,right in zip(bounds,bounds[1:]):
            overlap=max(overlap,left[1]-right[0])
        gap=min((right[0]-left[1] for left,right in zip(bounds,bounds[1:])),default=999)
        return gap,overlap,bounds
    cases=0;minimum=999;old_min=999;examples=[]
    for side in range(2):
        for reason in (0,2):
            for win in range(2):
                old=measure(special(before,side,reason,win));new=measure(special(after,side,reason,win))
                assert new[0]>=8 and not new[1],(side,reason,win,new)
                cases+=1;minimum=min(minimum,new[0]);old_min=min(old_min,old[0])
                examples.append((f'{"W" if side==0 else "B"} {"Time" if reason==0 else "Resign"} {"Win" if win==0 else "Loss"}',special(before,side,reason,win),special(after,side,reason,win)))
        for margin in range(1000):
            for half in (False,True):
                for win in range(2):
                    old=measure(point(before,side,margin,half,win));new=measure(point(after,side,margin,half,win))
                    assert new[0]>=6 and not new[1],(side,margin,half,win,new)
                    minimum=min(minimum,new[0]);old_min=min(old_min,old[0]);cases+=1
        for margin,half in [(1,False),(11,False),(101,False),(0,True),(6,True),(99,True),(999,True)]:
            examples.append((f'{"W" if side==0 else "B"} {margin}{".5" if half else ""}pt Win',point(before,side,margin,half,0),point(after,side,margin,half,0)))
    for index in (1,3):
        ts=[token(after,'win43_5.D4',index,65)]
        b=measure(ts)[2][0];assert 66<=b[0]<b[1]<=400
        cases+=1;examples.append((GRIDS['win43_5.D4'][2][index],[token(before,'win43_5.D4',index,65)],ts))
    # Move count retains original slots/advances. Check all 0..999 digit strings.
    for count in range(1000):
        ds=str(count);ts=[token(after,'win43_0.D4',int(d),32*i) for i,d in enumerate(ds)]
        ts.append(token(after,'win43_1.D4',0,32*len(ds)))
        assert measure(ts)[0]>=2,(count,measure(ts));cases+=1
    sheet=Image.new('RGBA',(1000,(len(examples)+1)*60),(55,55,55,255));draw=ImageDraw.Draw(sheet)
    draw.text((8,8),'Static atlas placement check: BEFORE (left) / AFTER (right). Not a Dolphin screenshot.',fill='white')
    for row,(label,old,new) in enumerate(examples,1):
        y=row*60;draw.text((5,y),label,fill='white')
        for offset,ts in [(0,old),(500,new)]:
            for im,x,text in ts:sheet.alpha_composite(im,(offset+x,y+15))
    sheet.convert('RGB').save(W/'result_spacing_comparison.png')
    result=dict(static_cases=cases,minimum_gap_after=minimum,minimum_gap_before=old_min,
                all_result_glyphs_common_baseline=30,move_count_baseline=28,
                no_extra_outline_or_resampling=True,
                coverage=['both colours','win/loss','resignation','timeout','jigo','draw','0..999 integer and half-point margins','0..999 moves'],
                limits=['Static placement model, not full renderer or runtime execution.',
                        'Native lower-row ordering of pt and .5 is retained; formatting order is outside this artwork-only correction.',
                        'Move-count native digit advances are retained; wide spacing is not tightened by code changes.'])
    (W/'layout_checks.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    return result

if __name__=='__main__':
    b=(W/'base_win.bin').read_bytes();lookup=dict(resources(b))
    changed,rows=edits(b)
    before={n:texture(b,lookup[n])[0] for n in GRIDS}
    for n,im in changed.items():im.save(W/('proposed_'+n+'.png'))
    (W/'atlas_changes.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
    print(layout_audit(before,changed))
