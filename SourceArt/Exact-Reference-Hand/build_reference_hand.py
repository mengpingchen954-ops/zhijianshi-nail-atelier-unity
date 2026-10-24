"""Reconstruct the actual reference silhouette, with a continuous editable hand mesh."""
import bpy,bmesh,json,math,hashlib,shutil
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
DATA=ROOT/'ModelData'
OUT=ROOT/'指间诗-原图轮廓重建.blend'
PREVIEW=Path('E:/Meijia/BlenderSource/Exact-Reference-Rebuild')
SOURCE=PROJECT/'SourceArt/CG-Hand-Refinement/指间诗工作室-纤长女生CG手-间距修正版.blend'
meta=json.loads((DATA/'measurements.json').read_text(encoding='utf-8'))
volume=np.load(DATA/'actual-reference-volume.npz')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
scene.name='Atelier · actual supplied reference reconstruction'
for o in list(bpy.data.objects):
    if o.name.startswith(('Hand_','Nail_','Study ·','Study key','Study fill','Study rim','Reference ·')):
        bpy.data.objects.remove(o,do_unlink=True)
for s in list(bpy.data.scenes):
    if s!=scene:bpy.data.scenes.remove(s)

def recalc(mesh):
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(mesh);bm.free();mesh.update()

def linear(rgb):
    return tuple(c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4 for c in rgb)+(1,)

def material(name,rgb,rough,kind='ceramic',metal=0):
    mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.diffuse_color=linear(rgb);mat['kind']=kind
    p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=mat.diffuse_color;p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return mat,p

def object_mesh(name,verts,faces,mat):
    m=bpy.data.meshes.new(name+' · editable mesh');m.from_pydata(verts,[],faces);recalc(m)
    o=bpy.data.objects.new(name,m);scene.collection.objects.link(o);m.materials.append(mat)
    for p in m.polygons:p.use_smooth=True
    return o

skin,p=material('Actual reference · soft rose skin',(.955,.789,.766),.43,'skin')
p.inputs['Subsurface Weight'].default_value=.095;p.inputs['Subsurface Scale'].default_value=.055
p.inputs['Subsurface Radius'].default_value=(1,.5,.38);p.inputs['Specular IOR Level'].default_value=.28
right=object_mesh('Hand_1',volume['vertices'].tolist(),volume['faces'].tolist(),skin)
bpy.ops.object.select_all(action='DESELECT');right.select_set(True);bpy.context.view_layer.objects.active=right
right.data.remesh_voxel_size=.0125
bpy.ops.object.voxel_remesh()
recalc(right.data)
polish=right.modifiers.new('Relax sampled voxel contour','SMOOTH');polish.factor=.4;polish.iterations=5
bpy.ops.object.modifier_apply(modifier=polish.name)
print('MEASURED_SURFACE_RETOPOLOGY',len(right.data.vertices),flush=True)
bpy.ops.object.quadriflow_remesh(target_faces=18000,use_mesh_symmetry=False,use_preserve_sharp=False,use_preserve_boundary=False,smooth_normals=True,seed=13)
print('CONTINUOUS_QUAD_HAND',len(right.data.vertices),flush=True)
assert len(right.data.polygons)>10000,'Retopology did not produce the expected continuous mesh'
assert all(len(poly.vertices)==4 for poly in right.data.polygons),'Retopology failed; do not ship the sampled triangle shell'
relax=right.modifiers.new('Polish measured contour','SMOOTH');relax.factor=.12;relax.iterations=2
bpy.ops.object.modifier_apply(modifier=relax.name)
for poly in right.data.polygons:poly.use_smooth=True
sub=right.modifiers.new('Editable smooth skin','SUBSURF');sub.levels=1;sub.render_levels=1
right.location=(1.72,0,.055)
uv=right.data.uv_layers.new(name='SkinUV')
x0,x1,y0,y1=meta['bounds'];wx,wy=meta['wrist'];scale=meta['scale']
for loop in right.data.loops:
    co=right.data.vertices[loop.vertex_index].co
    px=co.x/scale+wx;py=wy-(co.y-meta['wrist_y'])/scale
    uv.data[loop.index].uv=((px-x0)/(x1-x0),1-(py-y0)/(y1-y0))
uvnode=skin.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='SkinUV'
geom=skin.node_tree.nodes.new('ShaderNodeNewGeometry');xyz=skin.node_tree.nodes.new('ShaderNodeSeparateXYZ')
skin.node_tree.links.new(geom.outputs['Normal'],xyz.inputs[0])
factor=skin.node_tree.nodes.new('ShaderNodeMapRange');factor.inputs['From Min'].default_value=-.25;factor.inputs['From Max'].default_value=.25
skin.node_tree.links.new(xyz.outputs['Z'],factor.inputs['Value'])
images=[]
for oldim in list(bpy.data.images):
    if oldim.name.startswith(('cg-skin-dorsal.png','cg-skin-palmar.png')):bpy.data.images.remove(oldim)
for label in ('palmar','dorsal'):
    im=bpy.data.images.load(str(DATA/f'skin-{label}.png'),check_existing=False);im.name=f'cg-skin-{label}.png';im.pack()
    node=skin.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;node.extension='EXTEND'
    skin.node_tree.links.new(uvnode.outputs['UV'],node.inputs['Vector']);images.append(node)
mix=skin.node_tree.nodes.new('ShaderNodeMixRGB')
skin.node_tree.links.new(factor.outputs['Result'],mix.inputs[0]);skin.node_tree.links.new(images[0].outputs['Color'],mix.inputs[1]);skin.node_tree.links.new(images[1].outputs['Color'],mix.inputs[2]);skin.node_tree.links.new(mix.outputs[0],p.inputs['Base Color'])
left=right.copy();left.data=right.data.copy();left.name='Hand_0';scene.collection.objects.link(left);left.location.x=-1.72
for v in left.data.vertices:v.co.x*=-1
recalc(left.data)
for hand in (right,left):hand['reference']='Directly measured from supplied 2048x1144 hand sheet; not the earlier substitute image'
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();ev=right.evaluated_get(dg);m=ev.to_mesh()
bvh=BVHTree.FromPolygons([v.co.copy() for v in m.vertices],[tuple(p.vertices) for p in m.polygons]);ev.to_mesh_clear()

def ip(point):return Vector(((point[0]-wx)*scale,meta['wrist_y']+(wy-point[1])*scale,0))
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)

nailmat,p=material('Actual reference · sheer rose nail',(.89,.54,.55),.14,'polish')
p.inputs['Coat Weight'].default_value=.65;p.inputs['Coat Roughness'].default_value=.12
# Keep the established packed image name required by the Unity exporter.
im=bpy.data.images.new('Natural blush nail · UV new',width=128,height=256,alpha=True)
pixels=np.ones((256,128,4),dtype=np.float32)
for j in range(256):
    v=j/255
    for i in range(128):
        s=2*i/127-1;moon=.17*math.exp(-(s/.6)**2-(v/.12)**2)
        edge=smooth(.90,.985,v+.03*s*s)
        c=np.array([.91,.57,.60])*(1-moon)+np.array([.96,.78,.76])*moon
        edge=smooth(.90,.985,v+.03*s*s)
        c=c*(1-edge)+np.array([.98,.89,.87])*edge
        # A restrained broad manicure reflection is shared with the runtime natural-nail texture.
        shine=.42*math.exp(-((s+.46)/.12)**2)*smooth(.02,.17,v)*(1-smooth(.85,1,v))
        c=c*(1-shine)+np.ones(3)*shine
        pixels[j,i,:3]=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(DATA/'natural-blush-nail.png');im.file_format='PNG';im.save();im.pack()
old=bpy.data.images.get('Natural blush nail · UV')
if old:old.name='Previous natural nail image'
im.name='Natural blush nail · UV'
node=nailmat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;nailmat.node_tree.links.new(node.outputs['Color'],p.inputs['Base Color'])
nail_reports=[]
for finger,(name,f) in enumerate(meta['landmarks'].items()):
    root=ip(f['nail_root']);tip=ip(f['nail_tip']);along_xy=(tip-root).normalized()
    hit,normal,_,_=bvh.ray_cast(root+Vector((0,0,.6)),Vector((0,0,-1)),1.2)
    assert hit is not None,(name,'root outside measured skin')
    root.z=hit.z
    normal=normal.lerp(Vector((0,0,1)),.92 if finger else .50).normalized()
    if finger==0:
        normal=Vector((-along_xy.y,along_xy.x,0))*math.sin(math.radians(65))+Vector((0,0,1))*math.cos(math.radians(65))
    across=along_xy.cross(normal).normalized();along=normal.cross(across).normalized()
    length=(tip-ip(f['nail_root'])).length/max(.4,math.hypot(along.x,along.y))
    width=f['nail_width']*scale/max(.25,math.hypot(across.x,across.y))
    a,b=[],[]
    for v in (0,.12,.25,.38,.45):
        for s in (-.8,-.4,0,.4,.8):
            d=v*length;x=s*width*.5;q=root+along*d+across*x
            h,_,_,_=bvh.ray_cast(q+normal*.4,-normal,.8)
            if h is not None:a.append([1,d,x,x*x]);b.append((h-q).dot(normal))
    assert len(b)>=15,(name,len(b))
    coeff=np.linalg.lstsq(np.array(a),np.array(b),rcond=None)[0]
    def height(d,x):
        c=coeff
        result=c[0]+max(-.12,min(.04,c[1]))*d+max(-.05,min(.05,c[2]))*x-2.3*x*x
        return float(result)
    verts=[]
    for j in range(41):
        v=j/40;profile=(.84+.16*math.sin(math.pi*v))*(1-.19*smooth(.65,1,v))
        for i in range(25):
            s=2*i/24-1;cap=1-math.sqrt(max(0,1-s*s));d=v*length+.024*cap*(1-v)**3-.040*cap*v**3
            x=s*width*.5*profile;q=root+along*d+across*x+normal*(height(d,x)+.003+.004*(1-s*s))
            h,_,_,_=bvh.ray_cast(q+normal*.4,-normal,.8)

            verts.append(q)
    # A single offset preserves the analytic plate; per-vertex skin clamping creates ridged reflections.
    clearance=0
    for q in verts:
        h,_,_,_=bvh.ray_cast(q+normal*.4,-normal,.8)
        if h is not None:clearance=max(clearance,.003-(q-h).dot(normal))
    verts=[q+normal*clearance for q in verts]
    faces=[(j*25+i,j*25+i+1,(j+1)*25+i+1,(j+1)*25+i) for j in range(40) for i in range(24)]
    for hand in range(2):
        sign=-1 if hand==0 else 1
        o=object_mesh(f'Nail_{hand*5+finger:02}',[(q.x*sign+1.72*sign,q.y,q.z) for q in verts],faces,nailmat);o.location.z=.055
        if sum(poly.normal.z for poly in o.data.polygons)<0:
            bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
        uv=o.data.uv_layers.new(name='NailUV')
        for loop in o.data.loops:
            k=loop.vertex_index;uv.data[loop.index].uv=((k%25)/24,(k//25)/40)
        mod=o.modifiers.new('Thin nail plate','SOLIDIFY');mod.thickness=.0025;mod.offset=-1
        mod=o.modifiers.new('Editable rounded edge','SUBSURF');mod.levels=1;mod.render_levels=1
        o['finger']=name;o['measured_nail_width_pixels']=f['nail_width']
    nail_reports.append({'finger':name,'width':width,'length':length})

# Replace the heavy pink ribbed cuffs with the reference's pale gathered fabric.
cloth,_=material('Ivory rose · gathered chiffon',(.97,.89,.88),.67,'fabric')
def garment(name,cx,sections,ribs):
    bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
    n=192;verts=[];faces=[];count=len(sections)
    for inner in (False,True):
        for j,(y,rx,rz) in enumerate(sections):
            for k in range(n):
                a=math.tau*k/n;wave=math.cos(ribs*a+.22*math.sin(a*3))
                r=.016*(.5+.5*wave) if not inner else -.014
                flounce=.028*wave*(1-j/(count-1))**2
                verts.append((cx+(rx+r)*math.cos(a),y+flounce,.08+(rz+r)*math.sin(a)))
    for side in range(2):
        off=side*count*n
        for j in range(count-1):
            for k in range(n):
                a=off+j*n+k;b=off+j*n+(k+1)%n
                face=(a,b,b+n,a+n);faces.append(face if side==0 else tuple(reversed(face)))
    for end in (0,count-1):
        for k in range(n):
            a=end*n+k;b=end*n+(k+1)%n;faces.append((a,a+count*n,b+count*n,b))
    return object_mesh(name,verts,faces,cloth)
gold,_=material('Original oval chain · warm gold',(.83,.61,.26),.25,'metal',.82)
stone,p=material('Original rose cabochon',(.77,.38,.49),.20,'ceramic');p.inputs['Coat Weight'].default_value=.5
for h in range(2):
    sign=-1 if h==0 else 1;cx=1.72*sign
    garment(f'Cuff_{h}',cx,[(-1.75,.54,.255),(-1.82,.59,.28),(-1.94,.54,.25),(-2.05,.48,.22),(-2.13,.49,.22),(-2.22,.53,.245)],16)
    garment(f'Sleeve_{h}',cx,[(-2.19,.53,.24),(-2.32,.60,.29),(-2.50,.66,.32),(-2.75,.68,.32),(-3.03,.65,.30),(-3.30,.61,.28)],20)
    verts=[];faces=[];center=Vector((cx-.075*sign,-1.46,.066))
    def link(c,u,v,rx,ry):
        off=len(verts);w=u.cross(v).normalized()
        for i in range(20):
            a=math.tau*i/20;rad=(u*math.cos(a)+v*math.sin(a)).normalized();p=c+u*(rx*math.cos(a))+v*(ry*math.sin(a))
            for j in range(6):
                b=math.tau*j/6;verts.append(tuple(p+(rad*math.cos(b)+w*math.sin(b))*.006))
        for i in range(20):
            for j in range(6):
                a=off+i*6+j;b=off+((i+1)%20)*6+j
                faces.append((a,b,off+((i+1)%20)*6+(j+1)%6,off+i*6+(j+1)%6))
    for k in range(30):
        a=math.tau*k/30;c=center+Vector((.423*math.cos(a),0,.187*math.sin(a)))
        tangent=Vector((-.423*math.sin(a),0,.187*math.cos(a))).normalized()
        radial=Vector((math.cos(a),0,math.sin(a)))
        v=(Vector((0,1,0))*.8+radial*(.60 if k%2 else -.60)).normalized()
        link(c,tangent,v,.047,.026)
    charm=center+Vector((0,-.07,.203));link(charm,Vector((1,0,0)),Vector((0,1,0)),.056,.072)
    object_mesh(f'HandDetail_{h}_Bracelet',verts,faces,gold)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=charm)
    gem=bpy.context.object;gem.name=f'HandDetail_{h}_Rose';gem.scale=(.041,.055,.018);gem.data.materials.append(stone)
    for p in gem.data.polygons:p.use_smooth=True

# True open-pose views use one mesh. The illustrated bent side pose is not claimed as another orthographic view.
study=bpy.data.scenes.new('Actual reference · open pose study');study.world=bpy.data.worlds.new('Mauve studio')
study.world.use_nodes=True
bg=next(n for n in study.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.34,.31,.39,1);bg.inputs['Strength'].default_value=.20
for o in [right]+[bpy.data.objects[f'Nail_{i:02}'] for i in range(5,10)]:
    clone=o.copy();clone.data=o.data;study.collection.objects.link(clone);clone.name='Study · '+o.name
    clone.location.x-=1.72
for name,loc,energy,size in [('Study key',(-3,1,5),650,3),('Study fill',(4,-1,3),90,4),('Study rim',(3,1,1),450,2)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=energy;light.shape='DISK';light.size=size
    light.color=(1,.90,.86) if name=='Study key' else (.92,.94,1)
    o=bpy.data.objects.new(name,light);study.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
target=Vector((((x0+x1)/2-wx)*scale,meta['wrist_y']+(wy-(y0+y1)/2)*scale,.055))
light=bpy.data.lights.new('Study softbox','AREA');light.energy=400;light.shape='RECTANGLE';light.size=1.2;light.size_y=5
softbox=bpy.data.objects.new('Study softbox',light);study.collection.objects.link(softbox);softbox.location=(0,1.1,5);softbox.rotation_euler=(-softbox.location).to_track_quat('-Z','Y').to_euler()
for label,direction in [('dorsal',(0,0,8)),('palmar',(0,0,-8)),('radial',(-8,0,0)),('beauty',(-3,-2,7))]:
    c=bpy.data.cameras.new('Study · '+label);c.type='ORTHO';c.ortho_scale=(y1-y0)*scale
    o=bpy.data.objects.new('Study · '+label,c);study.collection.objects.link(o);o.location=target+Vector(direction)
    back=(o.location-target).normalized();up=Vector((0,1,0));horizontal=up.cross(back).normalized();up=back.cross(horizontal).normalized()
    o.rotation_euler=Matrix((horizontal,up,back)).transposed().to_euler()
study.camera=bpy.data.objects['Study · dorsal']
study.render.engine='CYCLES';study.cycles.samples=48;study.cycles.use_denoising=True
study.render.resolution_x=652;study.render.resolution_y=1236;study.render.resolution_percentage=100
study.render.image_settings.file_format='PNG';study.view_settings.view_transform='AgX'
scene['model_scope']='Actual reference silhouette and nail landmarks; original unbranded oval bracelet; pale gathered cuffs'
report={'reference':meta['reference'],'limit':meta['limit'],'source':str(OUT),'nails':nail_reports,'runtime_mesh_count':len([o for o in scene.objects if o.type=='MESH'])}
# Independently sample the evaluated skin against the measured hand mask.
mask=volume['mask'];intersection=union=0
for row in range(0,mask.shape[0],3):
    for col in range(0,mask.shape[1],3):
        px=x0+col/(mask.shape[1]-1)*(x1-x0);py=y0+row/(mask.shape[0]-1)*(y1-y0);q=ip((px,py))
        hit,_,_,_=bvh.ray_cast(q+Vector((0,0,.6)),Vector((0,0,-1)),1.2)
        predicted=hit is not None;expected=bool(mask[row,col]);intersection+=predicted and expected;union+=predicted or expected
report['actual_skin_silhouette_iou']=intersection/union
assert report['actual_skin_silhouette_iou']>.965,report['actual_skin_silhouette_iou']
for o in [right,left]+[bpy.data.objects[f'Nail_{i:02}'] for i in range(10)]:
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();bm=bmesh.new();bm.from_mesh(mesh)
    assert all(e.is_manifold for e in bm.edges),o.name
    assert bm.calc_volume(signed=True)>0,o.name
    bm.free();ev.to_mesh_clear()
bpy.context.window.scene=scene
bpy.ops.wm.save_as_mainfile(filepath=str(OUT));shutil.copy2(OUT,PREVIEW/OUT.name)
(ROOT/'geometry-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for label in ('dorsal','palmar','radial','beauty'):
    study.camera=bpy.data.objects['Study · '+label]
    rot=study.camera.rotation_euler.to_matrix()
    for name,loc in [('Study key',(-3,1,5)),('Study fill',(4,-1,3)),('Study rim',(3,1,1))]:
        o=bpy.data.objects[name];o.location=rot@Vector(loc);o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
    study.render.filepath=str(PREVIEW/f'rebuilt-{label}.png');bpy.ops.render.render(write_still=True,scene=study.name)
scene.cycles.samples=32;scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.filepath=str(PREVIEW/'rebuilt-studio.png');bpy.ops.render.render(write_still=True,scene=scene.name)
print('ACTUAL_REFERENCE_REBUILT',json.dumps(report,ensure_ascii=False),flush=True)
