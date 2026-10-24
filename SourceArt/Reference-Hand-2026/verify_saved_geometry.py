"""Independently reopen and inspect the delivered Blender source, without saving it."""
import bpy, bmesh, json, hashlib
from mathutils.bvhtree import BVHTree
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=ROOT/'指间诗-参考图手型与甲床优化.blend'
before=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
dg=bpy.context.evaluated_depsgraph_get()
report={}
trees={}
for name in [f'Hand_{i}' for i in range(2)]+[f'Nail_{i:02}' for i in range(10)]:
    o=bpy.data.objects[name]
    if name.startswith('Nail_'):
        assert len(o.data.vertices)==1025,name
        coords={(round(uv.uv.x*24),round(uv.uv.y*40)) for uv in o.data.uv_layers['NailUV'].data}
        assert len(coords)==1025,name
    ev=o.evaluated_get(dg);mesh=ev.to_mesh()
    if name.startswith('Hand_'):
        trees[name]=BVHTree.FromPolygons([o.matrix_world@v.co for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons])
    bm=bmesh.new();bm.from_mesh(mesh)
    bad=sum(not e.is_manifold for e in bm.edges)
    zero=sum(f.calc_area()<1e-12 for f in bm.faces)
    vol=bm.calc_volume(signed=True)
    assert bad==zero==0 and vol>0,(name,bad,zero,vol)
    report[name]={'closed_manifold':True,'zero_area_faces':zero,'volume':vol}
    bm.free();ev.to_mesh_clear()
assert not trees['Hand_0'].overlap(trees['Hand_1']),'Hands intersect in the atelier pose'
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
(ROOT/'saved-geometry-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SAVED_GEOMETRY_VERIFIED',len(report),'meshes; unchanged source SHA256',before)
