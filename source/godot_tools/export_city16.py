"""Concept 16 (approved 27 Nov 2026): city blocks with depth for the Godot game. Every glass-core tower of the map
(city16_plots.json: footprint, ground height, height of the old tower box, measured from the Towers group of the base
chunks) gets a building of the four concept 16 types (isle_towers_hq.fit) at the same size: towers of 100 m and more
become glass offices or mixed-use towers, the lower ones stone offices or residential towers. Merged per material per
400 m cell into godot/assets/island/city16/c16_<i>_<j>.glb, objects named City16__<material>.
run: python3 export_city16.py"""
import os, sys, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'source', 'blender'))
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
import isle_towers_hq as TW, isle_lib as L, isle_photo as PH
OUT = os.path.join(ROOT, 'godot', 'assets', 'island', 'city16'); os.makedirs(OUT, exist_ok=True)
plots = json.load(open(os.path.join(HERE, 'city16_plots.json')))
# kit material -> game material name: WindowGlass (rooms behind glass, lit at night), C16Glass (curtain walls, shaders/glass16),
# C16Stone/StoneDark/Render/Panel (kit shader), C16Light (glows at night), the rest plain materials
NAME = {'Glass': 'C16Glass', 'GlassDark': 'WindowGlass', 'GlassLobby': 'WindowGlass', 'GlassCrown': 'C16Glass', 'GlassRail': 'C16Rail',
        'Stone': 'C16Stone', 'StoneDark': 'C16StoneDark', 'Render': 'C16Render', 'Panel': 'C16Panel', 'Alu': 'C16Alu', 'Frame': 'C16Frame', 'FrameDark': 'C16FrameDark',
        'Spandrel': 'C16Spandrel', 'Coping': 'C16Coping', 'Plant': 'C16Plant', 'Tank': 'C16Plant', 'Louvre': 'C16Alu', 'Core': 'C16Core', 'Slab': 'C16Coping',
        'Band': 'C16Band', 'Canopy': 'C16Canopy', 'Timber': 'C16Timber', 'Foliage': 'C16Foliage', 'CrownLight': 'C16Light'}
COL = {'C16Rail': ((0.6, 0.7, 0.72), 0.05, 0.0), 'C16Stone': ((0.66, 0.55, 0.4), 0.8, 0.0), 'C16StoneDark': ((0.42, 0.35, 0.27), 0.85, 0.0), 'C16Render': ((0.86, 0.83, 0.77), 0.85, 0.0),
       'C16Panel': ((0.55, 0.5, 0.46), 0.6, 0.0), 'C16Alu': ((0.11, 0.115, 0.125), 0.42, 0.5), 'C16Frame': ((0.6, 0.6, 0.58), 0.45, 0.6), 'C16FrameDark': ((0.08, 0.08, 0.085), 0.4, 0.6),
       'C16Spandrel': ((0.08, 0.085, 0.09), 0.25, 0.4), 'C16Coping': ((0.4, 0.4, 0.39), 0.6, 0.2), 'C16Plant': ((0.55, 0.55, 0.53), 0.5, 0.4), 'C16Core': ((0.16, 0.16, 0.17), 0.9, 0.0),
       'C16Band': ((0.6, 0.6, 0.58), 0.5, 0.0), 'C16Canopy': ((0.15, 0.16, 0.17), 0.3, 0.8), 'C16Timber': ((0.4, 0.24, 0.12), 0.6, 0.0), 'C16Foliage': ((0.12, 0.25, 0.06), 0.85, 0.0),
       'C16Light': ((1.0, 0.92, 0.8), 0.3, 0.0), 'WindowGlass': ((0.05, 0.06, 0.07), 0.05, 0.0), 'C16Glass': ((0.04, 0.05, 0.06), 0.05, 0.0)}
TEX = {'C16Stone', 'C16StoneDark', 'C16Render', 'C16Panel'}
photo = L.make_image('c16_plaster', np.clip(PH.colour('Plaster003', 0.62, 0.5), 0, 1))
MATS = {}
def mat(nm):
    if nm in MATS: return MATS[nm]
    c, r, mt = COL[nm]; m = L.new_mat(nm, r, metal=mt, color=c, image=photo if nm in TEX else None, alpha=0.35 if nm == 'C16Rail' else 1.0)
    if nm in TEX: m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*c, 1)
    if nm == 'C16Light':
        b = m.node_tree.nodes['Principled BSDF']; b.inputs['Emission Color'].default_value = (*c, 1); b.inputs['Emission Strength'].default_value = 2.0
    MATS[nm] = m; return m

FACES = ((0, 1, 3, 2, 0), (4, 6, 7, 5, 0), (0, 4, 5, 1, 1), (2, 3, 7, 6, 1), (0, 2, 6, 4, 2), (1, 5, 7, 3, 2))   # quad + axis of its normal
cells = {}          # (i, j) -> material -> [verts, faces, uvs]
tris = 0; kinds = {}
for k, p in enumerate(sorted(plots, key=lambda q: (q['x'], q['z']))):
    tall = p['h'] >= 100.0
    kind = (['office_glass', 'mixed_tower'] if tall else ['office_stone', 'residential'])[(k * 7 + int(abs(p['x']) + abs(p['z']))) % 2]
    kinds[kind] = kinds.get(kind, 0) + 1
    B, fp, h = TW.fit(kind, p['w'] - 0.6, p['d'] - 0.6, p['h'], seed=k + 1)
    yaw = (k % 2) * math.pi          # half of them face the other way, so fronts are not all on one side
    ca, sa = math.cos(yaw), math.sin(yaw)
    org = np.array([p['x'], -p['z'], p['y0']])          # Blender: x, -z (glTF export turns it back), up
    key = (int(math.floor(p['x'] / 400.0)), int(math.floor(p['z'] / 400.0)))
    C = cells.setdefault(key, {})
    for km, boxes in B.items():
        nm = NAME[km]; e = C.setdefault(nm, [[], [], []])
        for c, s in boxes:
            c = np.array(c); hs = np.array(s) / 2
            cr = np.array([c[0] * ca - c[1] * sa, c[0] * sa + c[1] * ca, c[2]]) + org
            corners = []
            for dx in (-1, 1):
                for dy in (-1, 1):
                    for dz in (-1, 1):
                        v = hs * (dx, dy, dz); corners.append(cr + (v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca, v[2]))
            for a, b_, c_, d_, ax in FACES:
                if ax == 2 and (a == 0) and c[2] - hs[2] > 0.3 and nm != 'C16Rail': continue          # undersides of anything above head height: never seen... except canopies
                n0 = len(e[0]); q = [corners[i] for i in (a, b_, c_, d_)]
                e[0].extend(q); e[1].append((n0, n0 + 1, n0 + 2, n0 + 3))
                for v in q:          # world-space planar UVs, 4 m per repeat
                    if ax == 0: e[2].append((v[1] * 0.25, v[2] * 0.25))
                    elif ax == 1: e[2].append((v[0] * 0.25, v[2] * 0.25))
                    else: e[2].append((v[0] * 0.25, v[1] * 0.25))
                tris += 2
for key, C in cells.items():
    bpy.ops.wm.read_factory_settings(use_empty=True) if False else None
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    for nm, (V, F, U) in C.items():
        me = bpy.data.meshes.new('City16__' + nm); me.from_pydata([tuple(v) for v in V], [], F); me.update()
        uv = me.uv_layers.new(name='UVMap'); li = np.array([vi for f in F for vi in f]); UV = np.array(U)
        uv.data.foreach_set('uv', UV[li].astype(np.float32).ravel()); me.materials.append(mat(nm))
        ob = bpy.data.objects.new('City16__' + nm, me); bpy.context.scene.collection.objects.link(ob)
    for o in bpy.context.scene.objects: o.select_set(True)
    f = os.path.join(OUT, 'c16_%d_%d.glb' % key)
    bpy.ops.export_scene.gltf(filepath=f, export_format='GLB', use_selection=True, export_normals=True, export_yup=True, export_image_format='JPEG')
    print('cell', key, len(C), 'materials')
print('city16', len(plots), 'buildings', kinds, tris, 'tris')
