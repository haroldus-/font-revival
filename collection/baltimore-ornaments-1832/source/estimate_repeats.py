"""Measure repeated-border periods and place crop edges in quiet seams.
No drawn geometry is changed; full specimen strips remain separately retained.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
f=Path('collection/baltimore-ornaments-1832');m=json.loads((f/'font.json').read_text());r=json.loads((f/'source/tracing.json').read_text());inv=json.loads((f/'source/inventory.json').read_text());items={e['id']:e for e in inv['entries']};pages={};changes=[]
for i in m['icons']:
 it=items[i['id']]
 if not (85<=i['pdf_page']<=119 and 'tile' in i['tags'] and 'corner' not in i['tags']):continue
 e=r['glyphs'][chr(int(i['codepoint'],16))];file=e['file']
 if file not in pages:pages={file:Image.open(f/file).convert('L')}
 page=pages[file];x0,y0,x1,y1=e['box'];width=x1-x0;left=max(0,x0-2*width);right=min(page.width,x1+2*width)
 a=np.asarray(page.crop((left,y0,right,y1)))<170;v=a.sum(axis=0).astype(float);n=len(v)
 lo=max(4,round(width*.65));hi=min(n//3,round(width*1.5));scores=[]
 for period in range(lo,hi+1):
  first=v[:-period];second=v[period:];den=np.mean(first*first+second*second)+1e-9
  scores.append((float(np.mean((first-second)**2)/den)+.005*abs(period-width)/width,period))
 _,period=min(scores)
 candidates=range(max(1,x0-left-round(period*.45)),min(n-period-1,x0-left+round(period*.45))+1)
 norm=max(v.max(),1);start=min(candidates,key=lambda x:(v[x]+v[x+period])/norm+.04*abs((x+period/2)-(x0-left+width/2))/width)
 new=[left+start,y0,left+start+period,y1]
 # Retain the measured repeat interval rather than any adjacent partial motif.
 changes.append({'id':i['id'],'old_box':e['box'],'box':new,'period_native_pixels':period,'method':'Lowest-error horizontal repetition near the reviewed sort width, with crop seams placed at minimum vertical ink projection; visually reviewed.'})
 e['box']=it['box']=new;it['grid_box']=[v*1000/page.width for v in new];it['repeat_boundary']='Inferred crop interval measured from the observed repeated impression; complete source strip also retained.'
for name,data in [('source/tracing.json',r),('source/inventory.json',inv),('source/repeat-measurements.json',changes)]: (f/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('Aligned',len(changes),'repeat pieces')
