"""Exact accelerated Baltimore scan cleanup; canonical releases use font.ttx.
Install this directory's requirements.txt for optional source preparation.
Potrace, scaling, rounding and checked vector boolean operations are unchanged.
"""
import sys,json,time
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image,ImageFilter,ImageDraw,ImageOps
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/trace_specimen.py').is_file())
sys.path.insert(0,str(ROOT/'scripts'))
import trace_specimen as tracing
original=tracing.clean_crop
cached={};papers={}
def clean(image,entry):
 if 'component_min_area' not in entry or entry.get('fill_holes',8):return original(image,entry)
 key=json.dumps(entry,sort_keys=True)
 if key in cached:return cached[key]
 angle=entry.get('rotation',0)
 if angle not in (0,90,180,270):raise ValueError('Crop rotation must be a counterclockwise quarter turn.')
 radius=entry.get('paper_normalization_radius',0);paper_key=(tuple(entry['box']),angle,radius)
 if paper_key not in papers:
  crop=image.crop(entry['box']).convert('L')
  if angle:crop=crop.rotate(angle,expand=True)
  if radius:
   paper=Image.fromarray(ndimage.maximum_filter(np.asarray(crop),size=2*radius+1,mode='nearest')).filter(ImageFilter.GaussianBlur(radius/3))
   values=np.asarray(crop,dtype=np.float64);background=np.asarray(paper,dtype=np.float64)
   crop=Image.fromarray(np.clip(np.rint(values*255/np.maximum(background,1)),0,255).astype(np.uint8))
  papers[paper_key]=crop
 crop=papers[paper_key].copy();draw=ImageDraw.Draw(crop)
 for rect in entry.get('erase',[]):draw.rectangle(rect,fill=255)
 crop=ImageOps.expand(crop,border=4,fill=255).filter(ImageFilter.GaussianBlur(entry.get('blur',.55)))
 mask=crop.point(lambda v:0 if v<entry.get('threshold',135) else 255)
 if entry.get('ink_erosion',0):mask=mask.filter(ImageFilter.MaxFilter(2*entry['ink_erosion']+1))
 labels,n=ndimage.label(np.asarray(mask)==0)
 if not n:raise ValueError('No ink in crop: '+str(entry['box']))
 keep=np.bincount(labels.ravel())>=entry['component_min_area'];keep[0]=False
 if not keep.any():raise ValueError('No components survive crop cleanup: '+str(entry['box']))
 result=Image.fromarray(np.where(keep[labels],0,255).astype(np.uint8));cached[key]=result
 return result
tracing.clean_crop=clean
prepare=tracing.prepare_entry
def prepare_entry(task):
 cached.clear();papers.clear()
 if task[0] not in tracing._decoded_images:tracing._decoded_images.clear()
 start=time.perf_counter();result=prepare(task)
 print(task[-1],round(time.perf_counter()-start,2),'seconds',flush=True)
 return result
tracing.prepare_entry=prepare_entry
if __name__=='__main__':tracing.main()
