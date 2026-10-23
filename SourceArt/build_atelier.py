"""Original soft-film atelier. Unity=(Blender X,Z,Y). Preserves 美甲.blend."""
import bpy, bmesh, math, json, os, random
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SOURCE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get('ATELIER_UNITY_PROJECT',str(SOURCE.parent/'meijia' if SOURCE.name=='BlenderSource' else SOURCE.parent)))
REPORT=PROJECT.parent/'MigrationReports';REPORT.mkdir(exist_ok=True)
OUT=PROJECT/'Assets/NailAtelier/Art';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,hex,rough=.4,metal=0,kind='ceramic'):
 m=bpy.data.materials.new(name);m.diffuse_color=tuple(int(hex[i:i+2],16)/255 for i in (0,2,4))+(1,);m.use_nodes=True;m['kind']=kind
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not p:
  p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs[0],out.inputs['Surface'])
 p.inputs['Base Color'].default_value=tuple(c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4 for c in m.diffuse_color[:3])+(1,)
 p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 p.inputs['Coat Weight'].default_value=.3 if kind in ('ceramic','polish','glass') else .03;p.inputs['Coat Roughness'].default_value=.12
 if kind=='skin':p.inputs['Subsurface Weight'].default_value=.16;p.inputs['Subsurface Radius'].default_value=(1,.45,.25)
 if kind=='fabric':p.inputs['Sheen Weight'].default_value=.3
 return m
skin=mat('Peach skin','F4B89B',.62,kind='skin');cream=mat('Warm cream','FFF1DD',.26);wood=mat('Pale oak','E4BA8E',.42,kind='wood')
rose=mat('Pink enamel','E8ABB9',.23);fabric=mat('Blush cotton','EDD4D2',.9,kind='fabric');knit=mat('Ivory knit','F7E5D4',.87,kind='fabric');sleeve=mat('Pink sweater','DE9FAB',.9,kind='fabric')
gold=mat('Champagne','D4AF78',.28,.68);white=mat('Porcelain','FFF5E6',.2);sage=mat('Sage','9BAE82',.7);nailmat=mat('Syrup coral','F28F8F',.14,kind='polish');yellow=mat('Daisy hearts','F1CA70',.5);crease=mat('Joint blush','E6A48A',.65,kind='skin')
def finish(o,name,m):
 o.name=name;o.data.materials.clear();o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o
def apply(o,mod):bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
def uvball(name,loc,scale,m,segments=32,rings=20):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,m)
def box(name,loc,scale,m,bevel=.06):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  b=o.modifiers.new('Round silhouette','BEVEL');b.width=bevel;b.segments=6;apply(o,b)
  n=o.modifiers.new('Corner normals','WEIGHTED_NORMAL');n.keep_sharp=True;apply(o,n)
 return finish(o,name,m)
def cyl(name,loc,r,depth,m):
 bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=r,depth=depth,location=loc);o=bpy.context.object;b=o.modifiers.new('Soft rim','BEVEL');b.width=min(.035,depth*.12);b.segments=3;apply(o,b);return finish(o,name,m)
def tube(name,points,r,m):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=3;s=c.splines.new('POLY');s.points.add(len(points)-1)
 for p,co in zip(s.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');return finish(bpy.context.object,name,m)
def loft(name,sections,m,N=32):
 vs=[];fs=[]
 for x,y,z,w,d in sections:
  for k in range(N):a=math.tau*k/N;vs.append((x+w*math.cos(a),y,z+d*math.sin(a)))
 for j in range(len(sections)-1):
  for k in range(N):a=j*N+k;b=j*N+(k+1)%N;fs.append((a,b,b+N,a+N))
 fs.append(tuple(reversed(range(N))));fs.append(tuple((len(sections)-1)*N+k for k in range(N)))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],fs);mesh.update();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);return finish(o,name,m)
def join(parts,name,m):
 bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();return finish(bpy.context.object,name,m)
anchors=[]
for hand in range(2):
 cx=-1.72 if hand==0 else 1.72;sgn=1 if hand==0 else -1
 sec=[(-2.05,.38,.155),(-1.7,.405,.17),(-1.35,.44,.19),(-1.,.56,.22),(-.55,.76,.25),(-.05,.79,.245),(.25,.80,.205),(.48,.68,.155),(.60,.45,.085),(.62,.15,.015)]
 parts=[loft('Palm',[(cx,y,.025,w,d) for y,w,d in sec],skin)]
 specs=[(.55,.40,1.52,.20,-.075),(.14,.49,1.72,.205,-.02),(-.28,.41,1.55,.19,.04),(-.66,.21,1.20,.164,.10)]
 for j,(x,base,L,r,angle) in enumerate(specs,1):
  angle*=sgn;dx=-math.sin(angle);dy=math.cos(angle);sections=[]
  for k in range(33):
   t=-.20+1.20*k/32;tip=math.sqrt(max(.0001,1-((max(0,t-.89))/.115)**2)) if t>.89 else 1;rr=r*(1-.16*t)*tip*(1+.035*math.cos(t*math.pi*5))
   sections.append((cx+x*sgn+dx*t*L,base+dy*t*L,.025+.012*math.sin(t*math.pi)-.008*t,rr,rr*.82))
  parts.append(loft('Finger',sections,skin));t=(L-.43)/L;rz=.025+.012*math.sin(t*math.pi)-.008*t+r*(1-.16*t)*.82-.055
  anchors.append({'index':hand*5+j,'x':cx+x*sgn+dx*(L-.43),'y':rz,'z':-base-dy*(L-.43),'angle':angle*180/math.pi,'width':r*1.52,'length':.44,'curve':.055})
 angle=-.64*sgn;direction=Vector((-math.sin(angle),math.cos(angle),0));base=Vector((cx+.60*sgn,-.58,.035));L=1.48
 parts.append(uvball('Thenar',(cx+.55*sgn,-.40,.01),(.34,.58,.20),skin));thumb=[]
 for k in range(33):
  t=k/32;p=base+direction*(L*t);rr=.225*(1-.22*t)
  if t>.89:rr*=math.sqrt(max(.0001,1-((t-.89)/.115)**2))
  thumb.append((p.x,p.y,.025,rr,rr*.78))
 parts.append(loft('Thumb',thumb,skin));p=base+direction*(L-.44)
 anchors.append({'index':hand*5,'x':p.x,'y':.025+.225*(1-.22*(L-.44)/L)*.78-.055,'z':-p.y,'angle':angle*180/math.pi,'width':.345,'length':.46,'curve':.058})
 o=join(parts,'Hand_'+str(hand),skin);rem=o.modifiers.new('Continuous sculpt','REMESH');rem.mode='VOXEL';rem.voxel_size=.020;apply(o,rem)
 sm=o.modifiers.new('Soft organic skin','SMOOTH');sm.factor=.65;sm.iterations=8;apply(o,sm);dec=o.modifiers.new('Game resolution','DECIMATE');dec.ratio=.55;apply(o,dec)
 # Sculpt shallow joint folds into the skin, without floating line geometry.
 for vertex in o.data.vertices:
  p=vertex.co
  if p.z<.065:continue
  for x,baseY,L,r,angle in specs:
   angle*=sgn
   for t in [.38,.43,.70]:
    xx=cx+x*sgn-math.sin(angle)*t*L;yy=baseY+math.cos(angle)*t*L
    dx=p.x-xx;dy=p.y-yy;across=dx*math.cos(angle)+dy*math.sin(angle);along=-dx*math.sin(angle)+dy*math.cos(angle)
    if abs(across)<r*.72 and abs(along)<.05:
     p.z-=.0035*math.exp(-(along/.014)**2)*math.sqrt(1-(across/(r*.72))**2)
 cuff=loft('Cuff_'+str(hand),[(cx,-2.25,.005,.51,.255),(cx,-2.20,.005,.52,.26),(cx,-1.80,.005,.49,.23),(cx,-1.74,.005,.47,.22)],knit,64);ribs=[]
 for k in range(54):
  a=k*math.tau/54;points=[]
  for j in range(9):
   t=j/8;points.append((cx+(.518-.037*t)*math.cos(a),-2.21+t*.44,.005+(.263-.032*t)*math.sin(a)))
  ribs.append(tube('Rib',points,.012,knit))
 join([cuff]+ribs,'Cuff_'+str(hand),knit)
 loft('Sleeve_'+str(hand),[(cx,-3.3,-.015,.61,.29),(cx,-3.,-.015,.60,.30),(cx,-2.65,-.005,.57,.28),(cx,-2.22,.005,.52,.255)],sleeve,64)
anchors.sort(key=lambda a:a['index'])
for a in anchors:
 verts=[];uvs=[];faces=[];rows=32;cols=18;angle=math.radians(a['angle']);along=Vector((-math.sin(angle),math.cos(angle),0));across=Vector((math.cos(angle),math.sin(angle),0));root=Vector((a['x'],-a['z'],a['y']))
 for j in range(rows+1):
  v=j/rows;blend=min(1,v/.18);blend=blend*blend*(3-2*blend);half=.44+(.49*math.sqrt(min(1,(v+.04)/.12,(1.04-v)/.12))-.44)*blend
  for k in range(cols+1):
   u=k/cols;p=root+across*((u-.5)*2*half*a['width'])+along*(v*a['length']+.04*(1-math.sqrt(max(0,1-(2*u-1)**2)))*(1-v)**6);p.z+=.014+a['curve']*(1-((2*u-1)*2*half)**2);verts.append(tuple(p));uvs.append((u,v))
 for j in range(rows):
  for i in range(cols):k=j*(cols+1)+i;faces.append((k,k+1,k+cols+2,k+cols+1))
 mesh=bpy.data.meshes.new('Editable nail UV');mesh.from_pydata(verts,[],faces);mesh.update();uv=mesh.uv_layers.new(name='NailUV')
 for p in mesh.polygons:
  for li in p.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
 o=bpy.data.objects.new('Nail_'+str(a['index']).zfill(2),mesh);bpy.context.collection.objects.link(o);finish(o,o.name,nailmat)
box('Worktable',(0,0,-.49),(11,8,.28),wood,.18);box('WorkMat',(0,-.05,-.28),(6.65,5.8,.16),fabric,.18)
for x in [-3.23,3.23]:tube('Stitch',[(x,-2.72,-.193),(x,2.62,-.193)],.008,knit)
for y in [-2.77,2.67]:tube('Stitch',[(-3.18,y,-.193),(3.18,y,-.193)],.008,knit)
box('BottleShelf',(-2.88,3.05,-.25),(2.9,1.1,.2),wood,.12);box('ShelfBack',(-2.88,3.47,.02),(2.9,.1,.55),wood,.04)
for i,hex in enumerate(['D996AB','B6ACD7','90B8BB','E4C176']):
 x=-3.85+i*.65;y=3.02;m=mat('Polish '+str(i),hex,.18,kind='glass');box('PolishBottle_'+str(i),(x,y,.055),(.46,.44,.50),m,.095);box('BottleGlassBase_'+str(i),(x,y,-.15),(.47,.45,.08),cream,.035);cyl('BottleCap_'+str(i),(x,y,.62),.135,.65,white)
 for k in range(5):
  a=k*math.tau/5;uvball('BottleFlower',(x+.052*math.cos(a),y-.227,.06+.052*math.sin(a)),(.04,.009,.04),cream,12,8)
 uvball('FlowerHeart',(x,y-.235,.06),(.018,.012,.018),gold,12,8)
# Rounded hollow UV arch; the centre opening remains the curing destination.
vs=[];fs=[];steps=48
for y in [2.45,3.48]:
 for outer in [True,False]:
  for k in range(steps+1):
   t=math.pi*k/steps;vs.append((.6+(1.40 if outer else 1.18)*math.cos(t),y,-.16+(.84 if outer else .66)*math.sin(t)))
N=steps+1
for layer in range(4):
 for k in range(steps):
  if layer<2:a=layer*N+k;b=a+2*N
  else:a=(layer-2)*2*N+k;b=a+N
  fs.append((a,a+1,b+1,b))
for k in [0,steps]:fs.append((k,k+N,k+3*N,k+2*N))
mesh=bpy.data.meshes.new('Hollow UV lamp');mesh.from_pydata(vs,[],fs);mesh.update();o=bpy.data.objects.new('LampBody',mesh);bpy.context.collection.objects.link(o);finish(o,'LampBody',rose)
box('LampBase',(.6,2.94,-.20),(2.85,1.14,.12),white,.06);box('LampLight',(.6,2.92,.44),(1.70,.65,.025),mat('Lavender LED','D8CBFF',.35),.01);box('LampButton',(.6,2.95,.69),(.34,.22,.035),gold,.06)
# Shallow heart ceramic well with a rounded raised lip.
vs=[(3.92,1.35,-.22)];fs=[];N=96
def heart(a):return 16*math.sin(a)**3/17,(13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a))/17
for ring in range(1,10):
 r=ring/9
 for k in range(N):x,y=heart(math.tau*k/N);vs.append((3.92+x*.86*r,1.35+y*.88*r,-.22+.16*r**5))
for k in range(N):fs.append((0,1+k,1+(k+1)%N))
for j in range(8):
 for k in range(N):a=1+j*N+k;b=1+j*N+(k+1)%N;fs.append((a,b,b+N,a+N))
mesh=bpy.data.meshes.new('Heart dish');mesh.from_pydata(vs,[],fs);mesh.update();o=bpy.data.objects.new('Tray',mesh);bpy.context.collection.objects.link(o);finish(o,'Tray',cream);sol=o.modifiers.new('Porcelain thickness','SOLIDIFY');sol.thickness=.045;apply(o,sol)
rim=[]
for k in range(N+1):x,y=heart(math.tau*k/N);rim.append((3.92+x*.86,1.35+y*.88,-.055))
join([o,tube('Dish lip',rim,.025,cream)],'Tray',cream)
box('DisplayFrame',(3.91,-.40,-.19),(1.35,1.02,.13),rose,.08);box('DisplayBoard',(3.91,-.40,-.115),(1.19,.86,.02),cream,.02)
parts=[uvball('VaseCore',(-4.13,-1.25,-.02),(.34,.34,.40),white)]
for k in range(6):a=k*math.tau/6;parts.append(uvball('VasePetal',(-4.13+.22*math.cos(a),-1.25+.22*math.sin(a),-.04),(.20,.20,.35),white))
join(parts,'DaisyVase',white);cyl('VaseMouth',(-4.13,-1.25,.29),.14,.08,gold)
for i in range(5):
 a=i*2.4;x=-4.13+.24*math.cos(a);y=-1.25+.24*math.sin(a);z=.75+(.18 if i%2 else 0);tube('DaisyStem',[(-4.13,-1.25,.27),(x,y,z)],.015,sage)
 for k in range(10):t=k*math.tau/10;p=uvball('DaisyPetal',(x+.13*math.cos(t),y+.13*math.sin(t),z),(.13,.054,.027),cream,16,10);p.rotation_euler.z=t
 uvball('DaisyCentre',(x,y,z+.025),(.075,.075,.045),yellow,20,12)
 leaf=uvball('DaisyLeaf',((-4.13+x)/2,(-1.25+y)/2,.51),(.15,.05,.018),sage,16,10);leaf.rotation_euler.z=a
box('NailFile',(3.79,-1.76,-.13),(.35,1.75,.10),rose,.16).rotation_euler.z=.25;box('FileFace',(3.79,-1.76,-.075),(.29,1.59,.012),fabric,.13).rotation_euler.z=.25
tube('OrangeWoodStick',[(3.37,.20,-.15),(4.80,-.35,-.15)],.035,wood)
# Recalculate closed mesh normals before AO and native export.
for o in bpy.data.objects:
 if o.type=='MESH' and not o.name.startswith('Nail_'):
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
# World-space BVH AO is exported as vertex colours for the Unity material.
allvs=[];allfs=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.name.startswith('Nail_'):continue
 off=len(allvs);allvs.extend(o.matrix_world@v.co for v in o.data.vertices);allfs.extend(tuple(off+i for i in p.vertices) for p in o.data.polygons)
bvh=BVHTree.FromPolygons(allvs,allfs,all_triangles=False);directions=[]
for k in range(8):a=k*2.399963;z=(k+.5)/8;r=math.sqrt(1-z*z);directions.append(Vector((r*math.cos(a),r*math.sin(a),z)))
objects=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 mesh=o.data;mesh.calc_loop_triangles();vs=[];ns=[];uv=[];tri=[];colors=[];m=o.active_material;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');ao=[]
 for vertex in mesh.vertices:
  v=o.matrix_world@vertex.co;n=(o.matrix_world.to_3x3()@vertex.normal).normalized();tangent=n.cross(Vector((0,1,0)))
  if tangent.length<.01:tangent=n.cross(Vector((1,0,0)))
  tangent.normalize();bitangent=n.cross(tangent);occ=0
  if not o.name.startswith(('Nail_','HandDetail_')):
   for d in directions:
    hit,_,_,dist=bvh.ray_cast(v+n*.012,tangent*d.x+bitangent*d.y+n*d.z,.65)
    if hit is not None:occ+=.7*(1-dist/.65)
  ao.append(max(.52,1-occ/len(directions)))
 for t in mesh.loop_triangles:
  for li in reversed(t.loops):
   loop=mesh.loops[li];v=o.matrix_world@mesh.vertices[loop.vertex_index].co;n=(o.matrix_world.to_3x3()@mesh.vertices[loop.vertex_index].normal).normalized();vs.extend((v.x,v.z,v.y));ns.extend((n.x,n.z,n.y));uv.extend(tuple(mesh.uv_layers.active.data[li].uv) if mesh.uv_layers.active else (0,0));tri.append(len(tri));a=ao[loop.vertex_index];colors.extend((a,a,a,1))
 objects.append({'name':o.name,'vertices':[round(v,6) for v in vs],'normals':[round(v,6) for v in ns],'uv':[round(v,6) for v in uv],'triangles':tri,'colors':[round(v,4) for v in colors],'color':list(m.diffuse_color),'metallic':p.inputs['Metallic'].default_value,'roughness':p.inputs['Roughness'].default_value,'kind':m.get('kind','ceramic')})
for a in anchors:a['z']=-a['z']
with open(OUT/'atelier-meshes.json','w',encoding='utf-8') as f:json.dump({'objects':objects,'anchors':anchors},f,separators=(',',':'))
bpy.ops.export_scene.fbx(filepath=str(OUT/'Atelier.fbx'),use_selection=False,object_types={'MESH'},axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True;scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world.use_nodes=True;bg=next((n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND'),None)
if bg:bg.inputs['Color'].default_value=(.78,.73,.67,1);bg.inputs['Strength'].default_value=.45
for loc,energy,size,color in [((-3,-1,6),650,5,(1,.88,.76)),((4,3,5),400,4,(.87,.92,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=energy;o.data.shape='RECTANGLE';o.data.size=size;o.data.size_y=size*.65;o.data.color=color
bpy.ops.object.camera_add(location=(.05,-4.6,10));cam=bpy.context.object;cam.rotation_euler=(Vector((0,.35,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=10.6;scene.camera=cam
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(REPORT/'blender-soft3d-preview.png');bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'指间诗工作室.blend'));bpy.ops.render.render(write_still=True)
print('ATELIER_SOFT3D_EXPORTED',len(objects),sum(len(o['vertices'])//3 for o in objects))
