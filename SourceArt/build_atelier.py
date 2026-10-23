"""Original Blender mesh source. Unity coordinates: X, Z, -Y. Never modifies 美甲.blend."""
import bpy, math, json, os
from pathlib import Path
from mathutils import Vector
SOURCE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get('ATELIER_UNITY_PROJECT',str(SOURCE.parent/'meijia' if SOURCE.name=='BlenderSource' else SOURCE.parent)))
ROOT=str(PROJECT.parent)
os.makedirs(os.path.join(ROOT,'MigrationReports'),exist_ok=True)
OUT=str(PROJECT/'Assets'/'NailAtelier'/'Art')
os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,hex,rough=.45,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=tuple(int(hex[i:i+2],16)/255 for i in (0,2,4))+(1,);m.use_nodes=True
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not p:
  p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs[0],out.inputs['Surface'])
 p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m
skin=mat('Skin','DAB29D',.5);cream=mat('Cream','F5ECDD');wood=mat('Walnut','B99073');gold=mat('Champagne','CBA775',.26,.65);rose=mat('Rose','C896A4');nailmat=mat('Nail','DB9DAD',.16);sage=mat('Sage','B7C5B3');white=mat('Porcelain','E9E2D8');dark=mat('Handle','695149')
def finish(o,name,m):
 o.name=name;o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o
def uvball(name,loc,scale,m,segments=32,rings=20):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,m)
def box(name,loc,scale,m,bevel=.06):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  b=o.modifiers.new('Soft crafted edges','BEVEL');b.width=bevel;b.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
 return finish(o,name,m)
def cyl(name,loc,r,depth,m):
 bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=r,depth=depth,location=loc);return finish(bpy.context.object,name,m)
anchors=[]
for hand in range(2):
 cx=-1.55 if hand==0 else 1.55;sign=1 if hand==0 else -1
 parts=[uvball('Palm', (cx,-.25,.04),(.75,1.1,.23),skin),uvball('Wrist',(cx,-1.2,.0),(.44,.75,.18),skin)]
 # Thumb is inward on both hands, separate from the four straight fingers.
 for j,(x,L,r) in enumerate([(.72,1.05,.235),(.44,1.66,.145),(.1,1.85,.15),(-.24,1.71,.142),(-.55,1.38,.127)]):
  base=Vector((cx+x*sign,.05 if j==0 else .42,.06));angle=(-.7*sign if j==0 else -.025*sign*(j-2))
  direction=Vector((-math.sin(angle),math.cos(angle),0));mid=base+direction*(L*.43)
  p=uvball('Finger',mid,(r,L*.64,r*.78),skin);p.rotation_euler.z=angle;parts.append(p)
  tip=base+direction*(L*.91);anchors.append({'index':hand*5+j,'x':tip.x,'y':.2,'z':-tip.y,'angle':angle*180/math.pi})
 bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object
 rem=o.modifiers.new('Joined anatomical silhouette','REMESH');rem.mode='VOXEL';rem.voxel_size=.033;bpy.ops.object.modifier_apply(modifier=rem.name)
 sm=o.modifiers.new('Soft skin','SMOOTH');sm.factor=.75;sm.iterations=2;bpy.ops.object.modifier_apply(modifier=sm.name)
 # Keep the fingers separate after voxel union, with rounded slots at the webs.
 for gap in [.27,-.07,-.395]:
  cutter=box('Finger gap',(cx+gap*sign,1.95,.1),(.065,2.4,1),skin,.026)
  bpy.context.view_layer.objects.active=o
  cut=o.modifiers.new('Open finger web','BOOLEAN');cut.operation='DIFFERENCE';cut.solver='EXACT';cut.object=cutter;bpy.ops.object.modifier_apply(modifier=cut.name)
  bpy.data.objects.remove(cutter,do_unlink=True)
 dec=o.modifiers.new('Game resolution','DECIMATE');dec.ratio=.5;bpy.ops.object.modifier_apply(modifier=dec.name);finish(o,'Hand_'+str(hand),skin)
 box('Cuff_'+str(hand),(cx,-1.74,.0),(.95,.48,.43),cream,.09)
for a in anchors:
 # Top surfaces are UV grids; nails can be reshaped without changing UV paint.
 verts=[];uvs=[];faces=[];rows=32;cols=18
 for v in range(rows+1):
  q=v/rows;hw=.49*(math.sin(math.pi*(.15+q*.85))**.3)
  for u in range(cols+1):
   t=u/cols;verts.append(((t-.5)*2*hw*.36,q*.54,.025+.055*(1-(2*t-1)**2)));uvs.append((t,q))
 for j in range(rows):
  for i in range(cols):
   k=j*(cols+1)+i;faces.append((k,k+1,k+cols+2,k+cols+1))
 mesh=bpy.data.meshes.new('UV_Nail');mesh.from_pydata(verts,[],faces);mesh.update();uv=mesh.uv_layers.new(name='NailUV')
 for p in mesh.polygons:
  for li in p.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
 o=bpy.data.objects.new('Nail_'+str(a['index']).zfill(2),mesh);bpy.context.collection.objects.link(o);o.location=(a['x'],-a['z']-.45,.205);o.rotation_euler.z=-a['angle']*math.pi/180;finish(o,o.name,nailmat)
box('Worktable',(0,0,-.44),(10,7,.27),wood,.13);box('WorkMat',(0,.05,-.25),(7.5,5.6,.12),cream,.16)
cyl('Tray',(3,1.9,-.13),.75,.1,gold)
for i,m in enumerate([rose,sage,nailmat,gold]):
 cyl('PolishBottle_'+str(i),(-3+i*.48,2.45,-.03),.17,.4,m);cyl('BottleCap_'+str(i),(-3+i*.48,2.45,.31),.11,.3,dark)
box('LampBody',(0,2.65,.18),(2.8,1.15,.35),white,.15)
for x in [-1.3,1.3]:box('LampLeg', (x,2.65,-.02),(.18,1.1,.55),white,.06)
box('LampLight',(0,2.55,-.01),(2.35,.7,.03),mat('LED','CBC2FF'),.0)
box('DisplayFrame',(3.45,-.18,-.12),(1.45,1.08,.12),gold,.04);box('DisplayBoard',(3.45,-.18,-.05),(1.32,.95,.015),cream,.01)
uvball('Vase',(-3.7,-1.6,.0),(.28,.28,.35),white)
for i in range(4):
 p=cyl('Stem',(-3.7+i*.05,-1.6,.45),.012,.65,sage)
 for j in range(5):uvball('Petal',(-3.7+i*.05+.09*math.cos(j*1.257),-1.6+.09*math.sin(j*1.257),.8),(.1,.07,.04),rose,16,8)
box('NailFile',(-3,1,.0),(.24,1.1,.06),sage,.07)
cyl('ToolHandle',(2.65,.8,-.04),.035,1.3,gold).rotation_euler.x=math.pi/2
box('BrushHead',(2.65,1.5,-.04),(.12,.3,.04),dark,.01)
# Individual reusable sticker meshes, hidden in the Blender assembly but exported.
for kind in ['star','flower','heart','bow','butterfly','foil','gem','pearl','droplet']:
 o=uvball('Deco_'+kind,(12,0,0),(.06,.06,.035),gold,16,10);o.hide_render=True
 if kind in ['star','flower','foil']:
  bpy.data.objects.remove(o,do_unlink=True);N=10 if kind=='star' else 12;vs=[(0,0,.012)]+[(math.cos(k*math.tau/N)*(.07 if k%2==0 else .03),math.sin(k*math.tau/N)*(.07 if k%2==0 else .03),0) for k in range(N)]
  mesh=bpy.data.meshes.new(kind);mesh.from_pydata(vs,[],[(0,k+1,(k+1)%N+1) for k in range(N)]);o=bpy.data.objects.new('Deco_'+kind,mesh);bpy.context.collection.objects.link(o);o.location=(12,0,0);finish(o,o.name,gold)
# Export exact evaluated meshes for deterministic Unity native prefabs, plus standard FBX.
objects=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 mesh=o.data;mesh.calc_loop_triangles();vs=[];ns=[];uv=[];tri=[]
 for t in mesh.loop_triangles:
  for li in reversed(t.loops):
   loop=mesh.loops[li];v=o.matrix_world@mesh.vertices[loop.vertex_index].co;n=o.matrix_world.to_3x3()@loop.normal if hasattr(loop,'normal') else o.matrix_world.to_3x3()@mesh.vertices[loop.vertex_index].normal
   if o.name.startswith('Deco_'):v.x-=12
   vs.extend((v.x,v.z,-v.y));ns.extend((n.x,n.z,-n.y));uv.extend(tuple(mesh.uv_layers.active.data[li].uv) if mesh.uv_layers.active else (0,0));tri.append(len(tri))
 m=o.active_material;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');objects.append({'name':o.name,'vertices':vs,'normals':ns,'uv':uv,'triangles':tri,'color':list(m.diffuse_color),'metallic':p.inputs['Metallic'].default_value,'roughness':p.inputs['Roughness'].default_value})
with open(os.path.join(OUT,'atelier-meshes.json'),'w',encoding='utf-8') as f:json.dump({'objects':objects,'anchors':anchors},f,separators=(',',':'))
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'指间诗工作室.blend'))
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'Atelier.fbx'),use_selection=False,object_types={'MESH'},axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.world.color=(.45,.4,.35)
bpy.ops.object.light_add(type='AREA',location=(0,0,6));bpy.context.object.data.energy=700;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=6
bpy.ops.object.camera_add(location=(.1,-3.3,8));cam=bpy.context.object;cam.rotation_euler=(Vector((0,.4,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=9;scene.camera=cam
scene.render.filepath=os.path.join(ROOT,'MigrationReports','blender-model-preview.png');bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'指间诗工作室.blend'));bpy.ops.render.render(write_still=True)
print('ATELIER_MODELS_EXPORTED',len(objects),sum(len(o['vertices'])//3 for o in objects))
