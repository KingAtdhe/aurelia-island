"""Game copies: normalise size, make LOD0/LOD1 by collapse decimation, export one GLB per species
with nodes T_<species>_LOD0 / T_<species>_LOD1 (glTF Y-up, origin at base centre, front = +Z)."""
import bpy, sys, os, numpy as np

OUT = '/home/claude/tripo/out/'
GAME = '/home/claude/tripo/game/'; os.makedirs(GAME, exist_ok=True)

# species: (source, fit, size, tris LOD0, tris LOD1)
#   fit 'w' = largest horizontal extent, 'h' = height
SPEC = {
    'rock':                  ('rock_boulder', 'w', 2.0, 900, 220),
    'rock_b':                ('rock_stones', 'w', 2.5, 1000, 260),
    'rock_c':                ('rock_corner', 'h', 2.4, 1400, 360),
    'rock_t_slab':           ('rock_slab', 'w', 3.0, 1200, 300),
    'rock_t_cliff':          ('rock_cliff', 'h', 8.0, 2200, 600),
    'prop_house_t_village':  ('bld_house', 'h', 8.5, 5000, 1600),
    'prop_barn_hq':          ('bld_barn', 'h', 12.0, 5000, 1600),
    'prop_house_t_cafe':     ('bld_cafe', 'h', 5.4, 5000, 1600),
    'prop_house_t_light':    ('bld_lighthouse', 'h', 30.0, 6500, 2000),
    'prop_house_t_canopy_petrol': ('bld_petrol', 'h', 5.8, 5000, 1500),
}
which = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(SPEC)

for sp in which:
    src, fit, size, t0, t1 = SPEC[sp]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=OUT + src + '.glb')
    o = [x for x in bpy.data.objects if x.type == 'MESH'][0]
    for x in list(bpy.data.objects):
        if x != o: bpy.data.objects.remove(x)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    co = np.array([v.co[:] for v in o.data.vertices]); mn, mx = co.min(0), co.max(0)
    ext = mx - mn
    s = size / (max(ext[0], ext[1]) if fit == 'w' else ext[2])
    c = np.array([(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]])
    if sp.startswith('rock'):
        c[2] = mn[2] + 0.08 * ext[2]        # sink rocks a little so they sit in the ground
    o.data.vertices.foreach_set('co', ((co - c) * s).ravel()); o.data.update()
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    o.name = f'T_{sp}_LOD0'
    # LOD1 is made in the pack step (meshopt keeps texture seams)
    o.data.materials[0].name = 'T_' + sp
    o['lod1'] = t1
    print(sp, 'scale', round(s, 3), 'size', np.round(ext * s, 2), 'tris', tris)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=GAME + sp + '.glb', export_format='GLB', use_selection=True, export_image_format='JPEG',
                              export_jpeg_quality=90, export_apply=True, export_tangents=False, export_attributes=False, export_extras=True)
