"""Separate shared printed rules using measured straight-line centres."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
f=Path('collection/baltimore-cuts-1832');m=json.loads((f/'font.json').read_text());r=json.loads((f/'source/tracing.json').read_text());inv=json.loads((f/'source/inventory.json').read_text());items={i['id']:i for i in inv['entries']};page=None;audit=[]
for icon in m['icons']:
 if not icon['specimen_number'].startswith('357-') or icon['specimen_number']=='357-25':continue
 e=r['glyphs'][chr(int(icon['codepoint'],16))];x0,y0,x1,y1=e['box']
 if page is None:page=np.asarray(Image.open(f/e['file']).convert('L'));scale=page.shape[1]/1000
 # Search only immediately around the already reviewed rule coordinates.
 xs=np.arange(x0+round(5*scale),x1-round(5*scale));centre=(x0+x1)/2;ink=255-page;lines=[]
 for guess in [y0+round(2*scale),y1-round(2*scale)]:
  best=(-1,None,None)
  for slope in np.linspace(-.04,.04,33):
   for y in range(guess-round(3*scale),guess+round(3*scale)+1):
    ys=np.rint(y+slope*(xs-centre)).astype(int)
    score=np.minimum(ink[ys,xs],np.maximum(ink[ys-1,xs],ink[ys+1,xs])).mean()
    if score>best[0]:best=(score,y,slope)
  lines.append(best)
 # Keep half of each shared rule, with one native-pixel margin. Erasures are
 # rectangular scan masks only; no new lines or border geometry are drawn.
 rects=[]
 for top,(_,yc,slope) in zip([True,False],lines):
  last=None;begin=0
  for j,x in enumerate(range(x0,x1+1)):
   cut=round(yc+slope*(x-centre))-y0+(-1 if top else 1)
   if cut!=last or x==x1:
    if last is not None:
     rect=[begin,0,j-1,max(-1,last-1)] if top else [begin,max(0,last+1),j-1,y1-y0]
     if rect[3]>=rect[1] and rect[2]>=rect[0]:rects.append(rect)
    begin=j;last=cut
 e['erase']=rects;items[icon['id']]['cleanup']='Shared top and bottom rules separated at their measured line centres; no borders drawn.'
 audit.append({'id':icon['id'],'rule_centres':[[float(v) for v in line] for line in lines],'native_centre_x':centre,'method':'Maximum continuous dark rule within reviewed boundary neighbourhood; retains original line pixels.'})
for name,data in [('source/tracing.json',r),('source/inventory.json',inv),('source/primer-rule-measurements.json',audit)]: (f/name).write_text(json.dumps(data,indent=2)+'\n')
