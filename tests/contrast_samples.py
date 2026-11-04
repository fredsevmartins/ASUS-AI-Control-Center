from pathlib import Path
try:
    from PIL import Image
except ImportError:
    print('BLOCKED: provisioned Pillow is required for screenshot pixel sampling.')
    raise SystemExit(2)
import json,re,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/asus-ai-liquid-materials')
def lum(c):
    v=[x/255 for x in c];v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v];return sum(a*b for a,b in zip(v,[.2126,.7152,.0722]))
def ratio(a,b):
    a,b=sorted([lum(a),lum(b)]);return (b+.05)/(a+.05)
checks=[]
for record in json.loads((root/'samples.json').read_text()):
    im=Image.open(root/record['image']).convert('RGB')
    for t in record['texts']:
        fg=[float(v) for v in re.findall(r'[\d.]+',t['color'])][:3]
        bg=[im.getpixel((min(im.width-1,int(t['x']+t['width']*f)),min(im.height-1,int(t['y']+t['height']*.5)))) for f in [.25,.5,.75]]
        checks.append({**{k:record[k] for k in ['section','theme']},**t,'contrast':round(min(ratio(fg,b) for b in bg),2),'backgroundSamples':bg})
failed=[t for t in checks if t['contrast']<4.5]
report={'method':'Firefox DPR1 rendered backgrounds, text fill hidden; three samples per visible DOM text rectangle. Conservative 4.5:1 threshold for all text. Canvas, offscreen text, disabled controls, hover/focus, and assistive technology excluded. Background samples approximate glyph-area contrast, not a complete accessibility certification.','count':len(checks),'minimum':min(t['contrast'] for t in checks),'failures':failed,'checks':checks}
(root/'contrast.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['count','minimum','failures']},indent=2))

sys.exit(1 if failed else 0)
