"""Make a master/TrueType size proof for explicitly approximated icon glyphs."""
import argparse,json,math,sys
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/fontrevival.py').exists())
sys.path.insert(0,str(ROOT/'scripts'))
from outline_raster import rasterize
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('family');parser.add_argument('--font',type=Path);args=parser.parse_args()
f=ROOT/'collection'/args.family;m=json.loads((f/'font.json').read_text());folder=f/'source/truetype-glyphs'
font_file=args.font or f/'fonts'/(m['postscript_name']+'.ttf')
icons=[i for i in m['icons'] if (folder/(i['glyph']+'.json')).exists()]
fonts={};out=f/'specimens/format-comparison.pdf';pdf=canvas.Canvas(str(out),pagesize=(842,595),invariant=1,pageCompression=1);pdf.setTitle(m['name']+' — full-detail master and compact TrueType');pdf.setAuthor('Harold Lehmann');findings=[]
for icon in icons:
 sheet=Image.new('RGB',(1600,1050),'white');draw=ImageDraw.Draw(sheet);label=ImageFont.load_default(size=22);draw.text((24,16),icon['name']+' / '+icon['specimen_number'],font=label,fill='black')
 entry=json.loads((folder/(icon['glyph']+'.json')).read_text());draw.text((24,49),f"Full-detail master above; TrueType below. {entry['original_quadratic_points']:,} to {entry['approximate_quadratic_points']:,} points.",font=label,fill='black')
 for x,size in zip([24,250,550,1000],[48,96,192,384]):
  for row,ext in enumerate(['master','ttf']):
   key=(ext,size)
   y=110+row*440
   if ext=='master':
    svg=ET.parse(f/'svg'/(icon['id']+'.svg')).getroot().find('.//{http://www.w3.org/2000/svg}path').attrib['d']
    mask=rasterize(svg,math.ceil(entry['advance_width']*size/2048),size,size/2048,(0,1900*size/2048))
    sheet.paste('black',(x,round(y+380-1900*size/2048)),mask)
   else:
    if key not in fonts:fonts[key]=ImageFont.truetype(str(font_file),size)
    draw.text((x,y+380),chr(int(icon['codepoint'],16)),font=fonts[key],fill='black',anchor='ls')
   draw.text((x,y+390),f'{size}px',font=label,fill='black')
 pdf.drawImage(ImageReader(sheet),20,34,width=802,height=526);pdf.showPage()
 review=ROOT/'workspace/baltimore-extraction/review/formats';review.mkdir(exist_ok=True)
 sheet.save(review/(icon['id']+'.png'))
 findings.append({'id':icon['id'],'glyph':icon['glyph'],'sizes_px':[48,96,192,384],'master_sha256':entry['master_sha256'],'raster_em_pixels':entry['raster_em_pixels'],'points_before':entry['original_quadratic_points'],'points_after':entry['approximate_quadratic_points']})
pdf.save();(f/'source/truetype-review.json').write_text(json.dumps({'method':'Compare full-detail master with explicitly approved format-specific TTF simplification. Same em, advance and baseline; review every affected encoded icon.','icons':findings},indent=2)+'\n');print(out,len(icons),'icons',flush=True)
