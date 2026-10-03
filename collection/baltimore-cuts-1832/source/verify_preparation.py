import importlib.util,json,random
from pathlib import Path
from PIL import Image
p=Path(__file__).with_name('prepare.py');s=importlib.util.spec_from_file_location('fast',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
random.seed(1832);im=Image.frombytes('L',(71,53),bytes(random.randrange(256) for _ in range(71*53)));count=0
for radius in [0,1,4,12]:
 for rotation in [0,90,180,270]:
  for threshold in [165,205,230]:
   e={'box':[3,2,66,48],'rotation':rotation,'paper_normalization_radius':radius,'threshold':threshold,'component_min_area':3,'fill_holes':0,'blur':.3,'erase':[[1,1,7,9]]}
   assert m.original(im,e).tobytes()==m.clean(im,e).tobytes(),e;count+=1
f=Path('collection/baltimore-cuts-1832');e=next(iter(json.loads((f/'source/tracing.json').read_text())['glyphs'].values()));im=Image.open(f/e['file'])
for t in [165,205,230]:
 e=e|{'threshold':t};assert m.original(im,e).tobytes()==m.clean(im,e).tobytes();count+=1
print(count,'byte-identical masks: 48 synthetic configurations and 3 source thresholds',flush=True)
