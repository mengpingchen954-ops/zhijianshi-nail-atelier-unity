"""Export the approved CG scene through the project's existing Unity mesh contract."""
import bpy
import json
import math
import hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
SOURCE = PROJECT / 'SourceArt/Exact-Reference-Hand/指间诗-原图轮廓重建.blend'
ART = PROJECT / 'Assets/NailAtelier/Art'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
scene = bpy.context.scene
textures = ART / 'Textures/CGHands'
textures.mkdir(parents=True, exist_ok=True)
for source, target in [('cg-skin-dorsal.png', 'skin-dorsal.png'), ('cg-skin-palmar.png', 'skin-palmar.png'), ('Natural blush nail · UV', 'natural-blush-nail.png')]:
    image = bpy.data.images[source]
    assert image.packed_file, source
    (textures / target).write_bytes(image.packed_file.data)

for obj in scene.objects:
    if obj.name.startswith('Hand_'):
        # Keep the approved silhouette, with fewer evaluated triangles for the running game.
        decimate = obj.modifiers.new('Unity runtime triangle budget', 'DECIMATE')
        decimate.ratio = .50
    elif obj.name.startswith('Nail_'):
        # Runtime editing needs the fitted single UV surface, not a welded closed nail shell.
        for modifier in obj.modifiers:
            if modifier.type in ('SOLIDIFY', 'SUBSURF'):
                modifier.show_viewport = False
                modifier.show_render = False
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

def unity(p):
    return [round(p.x, 6), round(p.z, 6), round(p.y, 6)]

def vec(p):
    x, y, z = unity(p)
    return {'x': x, 'y': y, 'z': z}

def get_mesh(obj):
    return bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)

meshes = {o.name: get_mesh(o) for o in scene.objects if o.type == 'MESH'}
all_vertices, all_faces = [], []
for name, mesh in meshes.items():
    if name.startswith('Nail_'):
        continue
    obj = scene.objects[name]
    off = len(all_vertices)
    all_vertices.extend(obj.matrix_world @ v.co for v in mesh.vertices)
    all_faces.extend(tuple(off + i for i in p.vertices) for p in mesh.polygons)
occluders = BVHTree.FromPolygons(all_vertices, all_faces)
directions = [Vector((.53, .24, .81)).normalized(), Vector((-.53, .24, .81)).normalized(), Vector((.1, -.7, .71)).normalized(), Vector((0, .1, 1)).normalized()]
objects, anchors = [], []
for name, mesh in meshes.items():
    obj = scene.objects[name]
    mesh.calc_loop_triangles()
    normal_matrix = obj.matrix_world.to_3x3().inverted().transposed()
    world_vertices = [obj.matrix_world @ v.co for v in mesh.vertices]
    ao = []
    for vertex, point in zip(mesh.vertices, world_vertices):
        normal = (normal_matrix @ vertex.normal).normalized()
        tangent = normal.cross(Vector((0, 1, 0)))
        if tangent.length < .01:
            tangent = normal.cross(Vector((1, 0, 0)))
        tangent.normalize()
        bitangent = normal.cross(tangent)
        occ = 0
        if not name.startswith('Nail_'):
            for d in directions:
                _, _, _, distance = occluders.ray_cast(point + normal * .012, tangent * d.x + bitangent * d.y + normal * d.z, .5)
                if distance is not None:
                    occ += .55 * (1 - distance / .5)
        ao.append(max(.6, 1 - occ / len(directions)))
    vertices, normals, uv, colors, triangles = [], [], [], [], []
    unique = {}
    uv_layer = mesh.uv_layers.get('NailUV' if name.startswith('Nail_') else 'SkinUV') or mesh.uv_layers.active
    for triangle in mesh.loop_triangles:
        for li in reversed(triangle.loops):
            loop = mesh.loops[li]
            vi = loop.vertex_index
            normal = (normal_matrix @ mesh.corner_normals[li].vector).normalized()
            point = unity(world_vertices[vi])
            normal = unity(normal)
            coord = [round(float(x), 6) for x in uv_layer.data[li].uv] if uv_layer else [0, 0]
            key = tuple(point + normal + coord)
            if key not in unique:
                unique[key] = len(vertices) // 3
                vertices.extend(point)
                normals.extend(normal)
                uv.extend(coord)
                colors.extend([round(ao[vi], 4)] * 3 + [1])
            triangles.append(unique[key])
    material = obj.active_material
    bsdf = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    entry = {'name': name, 'vertices': vertices, 'normals': normals, 'uv': uv, 'triangles': triangles, 'colors': colors,
             'color': list(material.diffuse_color), 'metallic': bsdf.inputs['Metallic'].default_value,
             'roughness': bsdf.inputs['Roughness'].default_value, 'kind': material.get('kind', 'ceramic')}
    if name.startswith(('Cuff_', 'Sleeve_', 'HandDetail_')):
        entry['color'] = [c*12.92 if c<.0031308 else 1.055*c**(1/2.4)-.055 for c in material.diffuse_color[:3]]+[1]
    if name.startswith('Hand_'):
        entry.update(color=[1, 1, 1, 1], albedo='Assets/NailAtelier/Art/Textures/CGHands/skin-dorsal.png', backAlbedo='Assets/NailAtelier/Art/Textures/CGHands/skin-palmar.png')
    if name.startswith('Nail_'):
        entry.update(color=[1, 1, 1, 1], albedo='Assets/NailAtelier/Art/Textures/CGHands/natural-blush-nail.png')
        grid = {}
        for loop in mesh.loops:
            coord = uv_layer.data[loop.index].uv
            grid[(round(coord.x * 24), round(coord.y * 40))] = world_vertices[loop.vertex_index]
        assert len(grid) == 25 * 41, (name, len(grid))
        root, tip = grid[(12, 0)], grid[(12, 40)]
        along = (tip - root).normalized()
        across = (grid[(24, 20)] - grid[(0, 20)]).normalized()
        normal = across.cross(along).normalized()
        if normal.z < 0:
            normal.negate()
        a = {'index': int(name[-2:]), 'x': root.x, 'y': root.z, 'z': root.y, 'angle': math.degrees(math.atan2(-along.x, along.y)),
             'width': (grid[(24, 20)] - grid[(0, 20)]).length, 'length': (tip - root).length, 'curve': .018,
             'along': vec(along), 'across': vec(across), 'normal': vec(normal), 'columns': 24, 'rows': 40}
        anchors.append(a)
    objects.append(entry)
    print('EXPORTED', name, len(vertices) // 3, len(triangles) // 3, flush=True)
anchors.sort(key=lambda a: a['index'])
assert [a['index'] for a in anchors] == list(range(10))
assert len(objects) == 141
(ART / 'atelier-meshes.json').write_text(json.dumps({'objects': objects, 'anchors': anchors}, separators=(',', ':')), encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    obj.select_set(obj.type == 'MESH')
bpy.ops.export_scene.fbx(filepath=str(ART / 'Atelier.fbx'), use_selection=True, object_types={'MESH'}, axis_forward='-Z', axis_up='Y', add_leaf_bones=False, bake_anim=False)
report = {'source': str(SOURCE), 'source_sha256': source_hash, 'objects': len(objects), 'vertices': sum(len(o['vertices']) // 3 for o in objects), 'triangles': sum(len(o['triangles']) // 3 for o in objects), 'anchors': len(anchors), 'nail_contract': 'Fitted 24x40 UV surface; runtime edits sample the reference grid; oriented thumb axes.'}
(SOURCE.parent / 'unity-export-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
print('CG_UNITY_EXPORT_COMPLETE', json.dumps(report, ensure_ascii=False), flush=True)
