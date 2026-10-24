"""Refine the saved atelier without changing props, UVs or the running Blender document."""
import bpy
import bmesh
import hashlib
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
SOURCE = PROJECT / 'SourceArt/CG-Hand-Refinement/指间诗工作室-纤长女生CG手-间距修正版.blend'
OUT = ROOT / '指间诗-参考图手型与甲床优化.blend'
PREVIEW = Path('E:/Meijia/BlenderSource/Reference-Hand-2026')
PREVIEW.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

def digest(o):
    return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],
        [tuple(p.vertices) for p in o.data.polygons], [tuple(r) for r in o.matrix_world])).encode()).hexdigest()

props = {o.name: digest(o) for o in scene.objects if o.type == 'MESH' and not o.name.startswith(('Hand_', 'Nail_'))}

def smooth(a, b, x):
    t = max(0, min(1, (x-a)/(b-a)))
    return t*t*(3-2*t)

def gauss(x, c, r):
    return math.exp(-((x-c)/r)**2)

axes = [(-.55, .19, 2.01, -.24, .025, -.035),
        (-.055, .27, 2.245, -.005, .045, .005),
        (.435, .065, 1.935, .145, .025, -.025),
        (.79, -.34, 1.295, .295, .025, -.065)]
extra_lift=0

def warp(co):
    x, y, z = co
    shifts = Vector((0, 0, 0))
    centers = [cx+((.025 if cx<0 else .075)*max(0,min(1.07,(y-base)/(tip-base)))) for cx,base,tip,*_ in axes]
    distances = [abs(x-c) for c in centers]
    weights = [math.exp(-(d-min(distances))/.018) for d in distances]
    weight_sum = sum(weights)
    for k,(cx, base, tip, spread, rise, curl) in enumerate(axes):
        t = max(0, min(1.07, (y-base)/(tip-base)))
        center = cx + ((.025 if cx < 0 else .075) * t)
        weight = weights[k]/weight_sum * smooth(base-.12, base+.30, y)
        # Smooth taper and small unequal bends keep the fingers from reading as parallel rods.
        taper = .055 * smooth(.25, 1, t)
        delta = Vector((spread*t**1.25 - (x-center)*taper, rise*t,
                        (z-.015)*.15 + curl*t*t + .018*math.sin(math.pi*min(1,t))))
        shifts += delta * weight
    thumb_weight = smooth(-.55, -1.12, x) * (1-smooth(.45, .95, y))
    thumb_t = smooth(-.6, .48, y)
    thumb_delta = Vector((-.08*thumb_t, .09*thumb_t, -.015*thumb_t + (z-.02)*.12))
    shifts = shifts*(1-thumb_weight) + thumb_delta*thumb_weight
    result = Vector(co) + shifts
    palm = gauss(y, -.62, .72) * (1-smooth(.72, 1.04, abs(x)))
    dorsal = smooth(-.025, .12, z)
    palmar = 1-smooth(-.12, .025, z)
    result.z += .035 * palm * dorsal
    result.z -= palmar * (.027*gauss(x,-.52,.34)*gauss(y,-.64,.55)
                         +.018*gauss(x,.54,.27)*gauss(y,-.70,.61))
    # All anatomy changes fade out before the existing sleeve and cuff opening.
    result=Vector(co).lerp(result, smooth(-1.68,-1.05,y))
    result.z+=extra_lift*smooth(-1.68,-1.05,y)
    return result

right = bpy.data.objects['Hand_1']
left = bpy.data.objects['Hand_0']
for v in right.data.vertices:
    v.co = warp(v.co)
for hand in (right, left):
    if hand == left:
        for v, r in zip(hand.data.vertices, right.data.vertices):
            v.co = (-r.co.x, r.co.y, r.co.z)
    hand.data.update()
    hand['refinement'] = 'Reference-guided finger splay, distal taper, soft palm volume and asymmetric relaxed bends'
    hand['reference_limit'] = 'Artistic interpretation of the supplied hand sheet; not a scan or a pose rig.'

bpy.context.view_layer.update()
# The fuller palm needs a little room above the existing work mat; leave the cuff transition fixed.
mat=bpy.data.objects['WorkMat']
mat_top=max((mat.matrix_world@Vector(c)).z for c in mat.bound_box)
bottom=min((right.matrix_world@Vector(c)).z for c in right.evaluated_get(bpy.context.evaluated_depsgraph_get()).bound_box)
extra_lift=max(0,mat_top+.025-bottom)
for hand in (right,left):
    for vertex in hand.data.vertices:
        vertex.co.z+=extra_lift*smooth(-1.68,-1.05,vertex.co.y)
    hand.data.update()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = right.evaluated_get(dg)
m = ev.to_mesh()
bvh = BVHTree.FromPolygons([v.co.copy() for v in m.vertices], [tuple(p.vertices) for p in m.polygons])
ev.to_mesh_clear()

report = {'source_sha256': source_hash, 'unchanged_props': len(props), 'hands': {}, 'nails': []}
for finger in range(5):
    nail = bpy.data.objects[f'Nail_{finger+5:02}']
    # The control grid is ordered by V then U in the existing Blender source.
    root0 = nail.data.vertices[12].co - Vector((1.72,0,0))
    tip0 = nail.data.vertices[40*25+12].co - Vector((1.72,0,0))
    root0, tip0 = warp(root0), warp(tip0)
    along = (tip0-root0).normalized()
    old_across = nail.data.vertices[20*25+24].co - nail.data.vertices[20*25].co
    across = old_across.normalized()
    normal = across.cross(along).normalized()
    if normal.z < 0:
        normal.negate()
    if finger!=0:
        normal=normal.lerp(Vector((0,0,1)),.85).normalized()
    across = along.cross(normal).normalized()
    along = normal.cross(across).normalized()
    root = root0-along*(.055 if finger==0 else .070)
    length = (tip0-root0).length + (.115 if finger==0 else .135)
    width = old_across.length * (1.14 if finger==0 else 1.06)
    fit_a,fit_b=[],[]
    for v in (0,.15,.30,.45,.60):
        for s in (-.8,-.4,0,.4,.8):
            d=v*length;xx=s*width*.5
            p=root+along*d+across*xx
            h,_,_,_=bvh.ray_cast(p+normal*.4,-normal,.8)
            if h is not None:
                fit_a.append([1,d,xx,d*d,xx*xx,d*xx])
                fit_b.append((h-p).dot(normal))
    assert len(fit_b)>=15,(finger,len(fit_b))
    coeff=np.linalg.lstsq(np.array(fit_a),np.array(fit_b),rcond=None)[0]
    def bed_height(d,x):
        stop=length*.64
        dd=min(d,stop)
        a,b,c,e,f,g=coeff
        height=a+b*dd+c*x+e*dd*dd+f*x*x+g*dd*x
        if d>stop:height+=(d-stop)*max(-.12,min(.12,b+2*e*stop+g*x))
        return float(height)
    coordinates = []
    fit_clearances = []
    for j in range(41):
        v = j/40
        # Oval plate, rounded cuticle, gently tapered free edge: no rectangular root wings.
        profile = (.84+.16*math.sin(math.pi*v)) * (1-.24*smooth(.55,1,v))
        for i in range(25):
            s = 2*i/24-1
            cap = 1-math.sqrt(max(0,1-s*s))
            distance = v*length + .040*cap*(1-v)**3 - .065*cap*v**3
            xx=s*width*.5*profile
            p = root + along*distance + across*xx
            p += normal*(bed_height(distance,xx)+.0055+.010*(1-s*s))
            hit, _, _, _ = bvh.ray_cast(p+normal*.4,-normal,.8)
            if hit is not None:
                contact = (p-hit).dot(normal)
                if contact<.0055:p+=normal*(.0055-contact)
                fit_clearances.append((p-hit).dot(normal))
            coordinates.append(p)
    # Relax height only; keep the UV outline and hand orientation exactly reproducible.
    for _ in range(6):
        relaxed = [p.copy() for p in coordinates]
        for j in range(1,40):
            for i in range(1,24):
                k=j*25+i
                avg=sum((coordinates[k+d] for d in (-25,-1,1,25)),Vector())*.25
                relaxed[k] += normal * ((avg-coordinates[k]).dot(normal)*.5)
        coordinates=relaxed
    # Recheck against skin after relaxation so no smoothing step can bury the plate.
    for k,p in enumerate(coordinates):
        h,_,_,_=bvh.ray_cast(p+normal*.35,-normal,.7)
        if h is not None and (p-h).dot(normal)<.005:
            coordinates[k] += normal*(.005-(p-h).dot(normal))
    for hand in range(2):
        obj=bpy.data.objects[f'Nail_{hand*5+finger:02}']
        sign=-1 if hand==0 else 1
        for vertex,p in zip(obj.data.vertices,coordinates):
            vertex.co=(p.x*sign+sign*1.72,p.y,p.z)
        obj.data.update()
        # Height fitting is already relaxed; the old unrestricted smoothing shrank the cuticle.
        for mod in list(obj.modifiers):
            if mod.type=='SMOOTH':obj.modifiers.remove(mod)
            elif mod.type=='SOLIDIFY':mod.thickness=.003;mod.offset=-1
        obj['refinement']='Long oval fitted bed, rounded cuticle, thin free edge; 24x40 editable UV grid'
    report['nails'].append({'finger':finger,'width':width,'length':length,'supported_clearance_min':min(fit_clearances)})

for hand in (right,left):
    ev=hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=ev.to_mesh()
    bm=bmesh.new();bm.from_mesh(mesh)
    bad=sum(not e.is_manifold for e in bm.edges)
    zero=sum(f.calc_area()<1e-12 for f in bm.faces)
    volume=bm.calc_volume(signed=True)
    assert bad==zero==0 and volume>0,(hand.name,bad,zero,volume)
    report['hands'][hand.name]={'vertices':len(mesh.vertices),'nonmanifold':bad,'zero_area':zero,'volume':volume}
    bm.free();ev.to_mesh_clear()
for name,value in props.items():assert digest(bpy.data.objects[name])==value,name
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
scene['reference_refinement']='2026-10 supplied stylized feminine hand reference: silhouette, palm volume, fitted long oval nail beds'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
import shutil
shutil.copy2(OUT,PREVIEW/OUT.name)
(ROOT/'geometry-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

study=bpy.data.scenes['Hand Study · CG proportions and anatomy']
study.render.engine='CYCLES';study.cycles.samples=32;study.cycles.use_denoising=True
study.render.resolution_x=700;study.render.resolution_y=1000;study.render.resolution_percentage=100
study.view_layers[0].material_override=None
lights=[('Study key',Vector((-3,2,5))),('Study fill',Vector((4,-.5,3))),('Study rim',Vector((1,4,2)))]
for label in ('dorsal','palmar','radial'):
    study.camera=bpy.data.objects[f'Study · {label} orthographic']
    rot=study.camera.rotation_euler.to_matrix()
    for name,local in lights:
        light=bpy.data.objects[name];light.location=rot@local
        light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    study.render.filepath=str(PREVIEW/f'after-{label}.png')
    bpy.ops.render.render(write_still=True,scene=study.name)
scene.cycles.samples=32;scene.render.resolution_x=1280;scene.render.resolution_y=1000
scene.render.filepath=str(PREVIEW/'after-studio.png')
bpy.ops.render.render(write_still=True,scene=scene.name)
print('REFERENCE_HAND_REFINEMENT_COMPLETE',json.dumps(report),flush=True)
