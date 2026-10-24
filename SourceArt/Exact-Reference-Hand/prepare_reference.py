"""Measure the user's actual hand sheet, not the earlier generated substitute."""
import sys
sys.path.insert(0,'E:/Meijia/BlenderSource/.tools/modeling-python')
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
from skimage import measure

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'ModelData';DATA.mkdir(exist_ok=True)
PREVIEW=Path('E:/Meijia/BlenderSource/Exact-Reference-Rebuild');PREVIEW.mkdir(exist_ok=True)
REF=Path('C:/Users/CHENME~1/AppData/Local/Temp/codex-clipboard-3da19897-8eba-417b-93f7-61a4b9a34e8c.png')
if REF.exists():im=Image.open(REF).convert('RGB').resize((2048,1144))
else:
    im=Image.new('RGB',(2048,1144),(120,116,132))
    im.paste(Image.open(DATA/'dorsal-guide.png').convert('RGB'),(1248,10))
X0,X1,Y0,Y1=1248,1792,10,1040
SCALE=4.04/875
WX,WY=1603,900
landmarks={
 'thumb':{'axis':[[1439,604],[1395,494],[1335,413],[1286,379]],'widths':[33,30,25,19], 'nail_root':[1307,400],'nail_tip':[1276,368],'nail_width':14},
 'index':{'axis':[[1459,439],[1426,295],[1403,198],[1384,108]],'widths':[28,25,23,20], 'nail_root':[1398,153],'nail_tip':[1378,96],'nail_width':30},
 'middle':{'axis':[[1527,414],[1528,263],[1525,148],[1522,40]],'widths':[30,28,25,22], 'nail_root':[1520,87],'nail_tip':[1520,25],'nail_width':35},
 'ring':{'axis':[[1595,441],[1608,293],[1617,197],[1623,105]],'widths':[28,25,23,20], 'nail_root':[1614,153],'nail_tip':[1623,89],'nail_width':31},
 'little':{'axis':[[1652,505],[1691,379],[1718,297],[1735,225]],'widths':[25,23,20,17], 'nail_root':[1722,270],'nail_tip':[1740,210],'nail_width':27}}
H=780;W=round(H*(X1-X0)/(Y1-Y0))
rgb=np.array(im.crop((X0,Y0,X1,Y1)).resize((W,H))).astype(float)
PX,PY=np.meshgrid(np.linspace(X0,X1,W),np.linspace(Y0,Y1,H))
mask=(rgb[...,0]-rgb[...,1]>14)&(rgb[...,0]-rgb[...,2]>13)&(rgb[...,0]>145)
mask&=PY<879
mask=ndi.binary_fill_holes(mask)
labels,_=ndi.label(mask);sizes=np.bincount(labels.ravel());sizes[0]=0
mask=labels==sizes.argmax()
# Continue the measured wrist beneath the sleeve without incorporating jewelry or cloth into skin.
t=np.clip((PY-780)/120,0,1)
cx=1574.5+(1603-1574.5)*t
half=79.5+4.5*t
mask=np.where(PY>780,(abs(PX-cx)<half)&(PY<1033),mask)
for f in landmarks.values():
    tip=np.array(f['axis'][-1],float);axis=tip-np.array(f['axis'][-2]);axis/=np.linalg.norm(axis)
    du=(PX-tip[0])*(-axis[1])+(PY-tip[1])*axis[0]
    dv=(PX-tip[0])*axis[0]+(PY-tip[1])*axis[1]
    r=f['widths'][-1]
    # Hand cap stops beneath the measured free nail edge; the nail is a separate mesh.
    mask&=~((abs(du)<r*1.6)&(dv>-r)&((du/r)**2+((dv+r)/r)**2>1))
mask=ndi.gaussian_filter(mask.astype(float),.75)>.48
mask[[0,-1],:]=False;mask[:,[0,-1]]=False
step=(Y1-Y0)*SCALE/H
X=(PX-WX)*SCALE;Y=-1.74+(WY-PY)*SCALE
inside=ndi.distance_transform_edt(mask)*step
sdf=ndi.gaussian_filter(inside-ndi.distance_transform_edt(~mask)*step,.85)

def g(x,c,r):return np.exp(-((x-c)/r)**2)
radius=.55+.08*g(Y,-.45,.6)
top_amp=.125+.032*g(Y,-.3,.6)
bottom_amp=.137+.035*g(Y,-.4,.65)
center=np.full(X.shape,.008)
folds=np.zeros(X.shape)
for name,f in landmarks.items():
    points=np.array(f['axis'],float);best=np.full(X.shape,1e6);width=np.zeros(X.shape);fraction=np.zeros(X.shape)
    for j in range(3):
        a,b=points[j:j+2];d=b-a
        t=np.clip(((PX-a[0])*d[0]+(PY-a[1])*d[1])/np.dot(d,d),0,1)
        dist=np.hypot(PX-a[0]-t*d[0],PY-a[1]-t*d[1]);closer=dist<best
        width=np.where(closer,(f['widths'][j]*(1-t)+f['widths'][j+1]*t)*SCALE,width)
        fraction=np.where(closer,(j+t)/3,fraction);best=np.minimum(best,dist)
    w=np.exp(-(best/np.maximum(width/SCALE*1.15,1))**4)*np.clip(fraction/.20,0,1)
    radius=radius*(1-w)+width*w
    top_amp=top_amp*(1-w)+width*.82*w
    bottom_amp=bottom_amp*(1-w)+width*.94*w
    # Metacarpals are relaxed; the back view remains the reference's open-hand pose.
    center+=(.010*np.sin(fraction*np.pi)+(.012 if name=='thumb' else 0))*w
    for j in (1,2):
        q=points[j];axis=points[j+1]-points[j-1];axis/=np.linalg.norm(axis)
        along=((PX-q[0])*axis[0]+(PY-q[1])*axis[1])*SCALE
        across=(-(PX-q[0])*axis[1]+(PY-q[1])*axis[0])*SCALE
        folds+=(.0045 if j==1 else .0025)*g(along,0,.065)*g(across,0,f['widths'][j]*SCALE*.8)
cross=np.sqrt(np.clip(2*np.clip(inside/np.maximum(radius,.04),0,1)-np.clip(inside/np.maximum(radius,.04),0,1)**2,0,1))
# Each metacarpal follows the finger base toward the wrist, rather than a parallel ridge.
for start,end in [((1459,439),(1575,760)),((1527,414),(1590,755)),((1595,441),(1605,755)),((1652,505),(1620,750))]:
    ax,ay=start;bx,by=end;dx,dy=bx-ax,by-ay
    t=np.clip(((PX-ax)*dx+(PY-ay)*dy)/(dx*dx+dy*dy),0,1)
    distance=np.hypot(PX-ax-t*dx,PY-ay-t*dy)
    folds+=.007*g(distance,0,17)*np.sin(np.pi*t)**.7
top=center+(top_amp+folds)*cross
bottom=center-bottom_amp*cross
bottom-=.030*g(X,-.52,.25)*g(Y,-.45,.51)*cross
bottom-=.012*g(X,.13,.23)*g(Y,-.55,.50)*cross
# Give the wrist a circular, continuous forearm section instead of a thin slab.
w=np.clip((-Y-1.00)/.60,0,1);w=w*w*(3-2*w)
wrist_z=.146*np.sqrt(np.clip(1-((PX-cx)/half)**2,0,1))
top=top*(1-w)+(wrist_z+.008)*w
bottom=bottom*(1-w)+(-wrist_z+.008)*w
z=np.arange(-.29,.30,step,dtype=np.float32)
volume=np.minimum(sdf[...,None],np.minimum(top[...,None]-z,z-bottom[...,None])).astype(np.float32)
volume[[0,-1],:,:]=-step;volume[:,[0,-1],:]=-step
v,f,_,_=measure.marching_cubes(volume,0,spacing=(step,step,step),allow_degenerate=False)
world=np.empty_like(v);world[:,0]=(X0-WX)*SCALE+v[:,1]
world[:,1]=-1.74+(WY-Y0)*SCALE-v[:,0];world[:,2]=z[0]+v[:,2]
np.savez_compressed(DATA/'actual-reference-volume.npz',vertices=world,faces=f,mask=mask)
Image.fromarray(np.uint8(mask)*255).save(DATA/'measured-skin-silhouette.png')

# Original PBR albedo: broad pink color variation, without the substitute reference's baked white bands.
tw,th=512,1024
tx,ty=np.meshgrid(np.linspace(X0,X1,tw),np.linspace(Y0,Y1,th))
for side,base in [('dorsal',np.array([.955,.789,.766])),('palmar',np.array([.97,.795,.762]))]:
    blush=np.zeros(tx.shape)
    for f in landmarks.values():
        for j,strength in [(1,.18),(2,.13),(3,.32)]:
            px,py=f['axis'][j];blush+=strength*g(tx,px,38)*g(ty,py,37)
    blush=np.clip(blush,0,.45)
    c=base[None,None,:]*(1-blush[...,None])+np.array([.91,.615,.605])*blush[...,None]
    if side=='palmar':c+=.014*g(tx,1505,105)[...,None]*g(ty,591,115)[...,None]
    if side=='dorsal':
        source=np.array(im.crop((X0,Y0,X1,Y1)).resize((tw,th))).astype(float)/255
        valid=(source[...,0]-source[...,1]>.055)&(source[...,0]>.57)&(ty<780)
        # Keep subtle reference blush and crease information; geometry supplies the main lighting.
        soft=ndi.gaussian_filter(source,(1.5,1.5,0))
        delta=np.clip(soft-ndi.gaussian_filter(soft,(32,24,0)),-.08,.08)
        fade=np.clip((780-ty)/65,0,1);fade=fade*fade*(3-2*fade)
        c+=delta*.55*(valid*fade)[...,None]
    Image.fromarray(np.uint8(np.clip(c,0,1)*255)).save(DATA/f'skin-{side}.png')

marked=im.copy();draw=ImageDraw.Draw(marked)
for name,f in landmarks.items():
    draw.line([tuple(p) for p in f['axis']],fill='#00d8e8',width=2)
    for p in (f['nail_root'],f['nail_tip']):draw.ellipse((p[0]-3,p[1]-3,p[0]+3,p[1]+3),fill='yellow')
marked.crop((X0,Y0,X1,920)).save(PREVIEW/'measured-reference.png')
im.crop((X0,Y0,X1,880)).save(DATA/'dorsal-guide.png')
meta={'scale':SCALE,'wrist':[WX,WY],'bounds':[X0,X1,Y0,Y1],'wrist_y':-1.74,'landmarks':landmarks,
      'reference':'Actual user attachment, 2048x1144; dorsal silhouette and nail landmarks measured directly',
      'limit':'Palm and side show different poses; depth is sculpted anatomical interpretation, not an exact multiview scan.'}
(DATA/'measurements.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print('ACTUAL_REFERENCE_VOLUME',len(world),len(np.load(DATA/'actual-reference-volume.npz')['faces']),'bounds',world.min(0),world.max(0))
