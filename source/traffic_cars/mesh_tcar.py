"""Blender stage: decimate the marched body, add wheels, project the reference sheet, export GLB (LOD0 / LOD1).
Car frame in the npz: x from the nose (0) to the tail (L), y = left, z up. Exported nose along glTF +Z."""
import bpy, bmesh, sys, json, math, numpy as np
name = sys.argv[sys.argv.index('--') + 1]
OUT = '/home/claude/tcars/out/'
J = json.load(open(OUT + name + '.json')); d = np.load(OUT + name + '_mc.npz')
L, H, W, AW, AH = J['L'], J['H'], J['W'], J['AW'], J['AH']
bpy.ops.wm.read_factory_settings(use_empty=True)

def car_to_b(p):           # car (x, y, z) -> Blender (x = left, y = x - L/2 so the nose points to -Y, z)
    return (p[1], p[0] - L / 2, p[2])

me = bpy.data.meshes.new('body'); v = d['v']; f = d['f']
me.from_pydata([car_to_b(p) for p in v], [], [tuple(x) for x in f]); me.update()          # marching-cubes winding is consistent; the axis swap makes it face outward
body = bpy.data.objects.new('body', me); bpy.context.scene.collection.objects.link(body)
bpy.context.view_layer.objects.active = body; body.select_set(True)
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(me); bm.free()
m = body.modifiers.new('s', 'SMOOTH'); m.iterations = 6; m.factor = 0.5; bpy.ops.object.modifier_apply(modifier='s')
tris = len(me.polygons); m = body.modifiers.new('d', 'DECIMATE'); m.ratio = 5200 / tris; bpy.ops.object.modifier_apply(modifier='d')

# wheels
R = J['R']
for wx, wz, wr in J['wheels']:
    for side in (1, -1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=wr * 0.98, depth=0.24, location=(side * (W / 2 - 0.15), wx - L / 2, wr), rotation=(0, math.pi / 2, 0))
        w = bpy.context.object; w.name = 'wheel'
bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
car = bpy.context.object; car.name = 'LOD0'

# projection: each face takes the view it faces most
def side_uv(bx, by, bz):
    x = by + L / 2; u = x / L; vv = bz / H
    sx, sy, sw, sh = J['side']; return ((sx + u * sw) / AW, 1 - (sy + (1 - vv) * sh) / AH)
TOP = np.array(J['top'])
def top_uv(bx, by):          # surfaces facing up: the colour just inside the top outline of the side view at this length
    x = np.clip((by + L / 2) / L, 0, 0.999); r = TOP[int(x * len(TOP))] + 8.0 / (J['side'][3] or 1) * 0
    sx, sy, sw, sh = J['side']; row = (TOP[int(x * len(TOP))] * sh + 7)
    return ((sx + x * sw) / AW, 1 - (sy + row) / AH)
def end_uv(region, bx, bz, flip):
    rx, ry, rw, rh = J[region]; fw_m = W * 1.12
    u = 0.5 + (bx / fw_m) * (-1 if flip else 1); vv = bz / H
    return ((rx + np.clip(u, 0, 1) * rw) / AW, 1 - (ry + (1 - np.clip(vv, 0, 1)) * rh) / AH)
for u in list(car.data.uv_layers): car.data.uv_layers.remove(u)
bm = bmesh.new(); bm.from_mesh(car.data); uv = bm.loops.layers.uv.new('UVMap')
for fc in bm.faces:
    n = fc.normal; ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
    fc_up = fc.calc_center_median().z > 0.62 * H and n.z > 0.3 and ay > ax
    for lp in fc.loops:
        c = lp.vert.co
        if fc_up and n.y < -0.2: lp[uv].uv = end_uv('front', c.x, c.z, False)          # windscreen: glass from the front view
        elif fc_up and n.y > 0.2: lp[uv].uv = end_uv('rear', c.x, c.z, True)          # rear window
        elif n.z > 0.72: lp[uv].uv = top_uv(c.x, c.y)                                       # bonnet, roof, windscreen from above
        elif n.z < -0.6 or ax >= ay: lp[uv].uv = side_uv(c.x, c.y, c.z)                  # sides: the side view
        elif n.y < 0: lp[uv].uv = end_uv('front', c.x, c.z, False)           # nose faces -Y; car's left (+X) shows on the right of the front view
        else: lp[uv].uv = end_uv('rear', c.x, c.z, True)
    fc.smooth = True
bm.to_mesh(car.data); bm.free()
mat = bpy.data.materials.new('TCar_' + name); mat.use_nodes = True; nt = mat.node_tree; b = nt.nodes['Principled BSDF']
t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(OUT + name + '_atlas.png'); nt.links.new(t.outputs[0], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.42; b.inputs['Metallic'].default_value = 0.0
car.data.materials.clear(); car.data.materials.append(mat)
lod1 = car.copy(); lod1.data = car.data.copy(); lod1.name = 'LOD1'; bpy.context.scene.collection.objects.link(lod1)
bpy.ops.object.select_all(action='DESELECT'); lod1.select_set(True); bpy.context.view_layer.objects.active = lod1
m = lod1.modifiers.new('d', 'DECIMATE'); m.ratio = 0.28; bpy.ops.object.modifier_apply(modifier='d')
print(name, 'LOD0 tris', sum(len(p.vertices) - 2 for p in car.data.polygons), 'LOD1 tris', sum(len(p.vertices) - 2 for p in lod1.data.polygons))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT + name + '.glb', export_format='GLB', use_selection=True, export_image_format='JPEG', export_jpeg_quality=88, export_tangents=False)
