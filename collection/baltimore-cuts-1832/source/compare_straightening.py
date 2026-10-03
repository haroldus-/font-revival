"""Render the saved before drawings and current rotated masters at display sizes.

Run from the repository root after straighten.py; workspace backup is retained.
"""
import argparse,json,math,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
sys.path.insert(0,'scripts');from outline_raster import rasterize
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--family',type=Path,default=Path('collection/baltimore-cuts-1832'))
parser.add_argument('--workspace',type=Path,default=Path('workspace/baltimore-extraction/straighten'))
args=parser.parse_args()
p=args.family;out=args.workspace;rows=[d for d in json.loads((p/'source/straightening.json').read_text())['icons'] if d['status']=='rotate'];m=json.loads((p/'font.json').read_text());icons={i['id']:i for i in m['icons']}
pdf=canvas.Canvas(str(p/'specimens/straightening-review.pdf'),pagesize=(842,595),invariant=1,pageCompression=1);pdf.setTitle(m['name']+' | Horizontal alignment review');pdf.setAuthor('Harold Lehmann')
font=ImageFont.load_default(size=22)
contacts=[]
for j,row in enumerate(rows):
 name=row['glyph'];before=json.loads((out/'before/source/glyphs'/(name+'.json')).read_text());after=json.loads((p/'source/glyphs'/(name+'.json')).read_text());width=before['advance_width'];sheet=Image.new('RGB',(1600,1050),'white');draw=ImageDraw.Draw(sheet)
 draw.text((24,14),f"{row['id']} | {icons[row['id']]['name']}",font=font,fill='black');draw.text((24,48),f"Before (top), after (bottom): {row['angle_degrees']:+.3f} degrees | {row['reference']}",font=font,fill='black')
 for col,size in enumerate([48,96,192,384]):
  x=[24,250,550,1000][col]
  for r,data in enumerate([before,after]):
   y=110+r*440;mask=rasterize(data['path'],math.ceil(width*size/2048),size,size/2048,(0,1900*size/2048));sheet.paste('black',(x,round(y+380-1900*size/2048)),mask)
   draw.line((x,y+380,x+max(mask.width,70),y+380),fill=(100,180,235));draw.text((x,y+390),f'{size}px',font=font,fill='black')
 sheet.save(out/(row['id']+'-review.png'));pdf.drawImage(ImageReader(sheet),20,34,width=802,height=526);pdf.showPage()
 # Larger side-by-side proof at 192px for the survey sheets.
 pair=Image.new('RGB',(700,250),'white');pd=ImageDraw.Draw(pair);pd.text((8,4),f"{row['specimen_number']} | {row['angle_degrees']:+.3f} degrees",font=ImageFont.load_default(size=18),fill='black')
 for c,data in enumerate([before,after]):
  size=192;mask=rasterize(data['path'],math.ceil(width*size/2048),size,size/2048,(0,1900*size/2048));pair.paste('black',(c*350+(350-mask.width)//2,40),mask)
 contacts.append(pair)
 print(j+1,row['id'],flush=True)
pdf.save()
for start in range(0,len(contacts),16):
 sheet=Image.new('RGB',(1400,8*250),'white')
 for j,pair in enumerate(contacts[start:start+16]):sheet.paste(pair,(j%2*700,j//2*250))
 sheet.save(out/f'final-{start:03d}.png')
print('Completed review PDF',len(rows),flush=True)
