"""Concept 15 (approved 27 Nov 2026): the concept 04 trees for the Godot game, replacing the Tripo trees on the roads.
Builds plane, plane_b, oak, oak_b, pine (Norway spruce), fruit (olive) and cypress with isle_trees_hq at game weight
(LOD0 = lod 2) and far weight (LOD1 = lod 1), the same seeds as the web game's map (isle_flora.HQMAP), and writes
godot/assets/island/flora_trees15.glb with S_h_<species>_LOD0/1 nodes (materials LeavesHQ and Bark_<kind>).
flora.gd loads it and points those species at the h_ models. run: python3 export_trees15.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'source', 'blender'))
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
import isle_flora as FL
NAMES = ['plane', 'plane_b', 'oak', 'oak_b', 'pine', 'fruit', 'cypress']
mats = {}; total = {}
for nm in NAMES:
    e = FL._build_hq(nm, mats)
    for lod in (0, 1):
        ob = e['lod%d' % lod]; ob.name = 'S_h_%s_LOD%d' % (nm, lod); ob.location = (0, 0, 0)
    total[nm] = (e['t0'], e['t1'], round(e['h'], 1))
# the atlas's see-through texels are white: mipmaps would bleed that into the leaves as a pale fringe at a distance.
# Fill them with the average leaf colour instead (the alpha is kept, so the cut-out shapes do not change).
import numpy as np
im = bpy.data.images['leaf_atlas_hq']; px = np.array(im.pixels[:], np.float32).reshape(-1, 4)
solid = px[:, 3] > 0.5; avg = px[solid, :3].mean(0); px[~solid, :3] = avg; im.pixels.foreach_set(px.ravel()); im.update()
# the map pipeline stores vertex colours linear (glTF), the plant builder writes them as display colours: convert
for o in bpy.context.scene.objects:
    ca = o.data.color_attributes.get('Col')
    if ca is None: continue
    c = np.empty(len(ca.data) * 4, np.float32); ca.data.foreach_get('color', c); c = c.reshape(-1, 4); c[:, :3] = np.clip(c[:, :3], 0, 1) ** 2.2
    ca.data.foreach_set('color', c.ravel())
for o in bpy.context.scene.objects: o.select_set(True)
out = os.path.join(ROOT, 'godot', 'assets', 'island', 'flora_trees15.glb')
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_vertex_color='ACTIVE', export_normals=True,
                          export_image_format='AUTO', export_apply=False, export_yup=True)
print('trees15', out, total)
