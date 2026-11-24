# Grass for the Godot game, modelled blade by blade (no alpha cards): five clump types for the island's ground,
# each a LOD0 (full clump) and a LOD1 (a third of the blades, a little wider) for the ring further out.
# Vertex colour = blade colour (root dark -> tip light); UV.y = height along the blade (0 root, 1 tip) for the wind in the game.
# Writes grass.glb and the art sheet (renders of each type + palette) with:  python3 grass_models.py <out dir>
import bpy, bmesh, math, random, sys, os, mathutils
OUT = sys.argv[-1] if sys.argv[-1].startswith('/') else '/home/claude/grass/'
# name: blades, radius, height (min,max), width, bend, lean, root colour, tip colour, dry share, extra
TYPES = {
	'meadow': dict(n=60, r=0.34, h=(0.30, 0.60), w=0.017, bend=0.55, lean=0.32, root=(0.16, 0.26, 0.08), tip=(0.55, 0.72, 0.28), dry=0.12, seed=1),
	'lawn':   dict(n=90, r=0.36, h=(0.10, 0.20), w=0.012, bend=0.25, lean=0.42, root=(0.15, 0.27, 0.08), tip=(0.48, 0.68, 0.24), dry=0.04, seed=2),
	'dry':    dict(n=48, r=0.32, h=(0.28, 0.55), w=0.014, bend=0.65, lean=0.35, root=(0.32, 0.28, 0.12), tip=(0.86, 0.74, 0.45), dry=0.85, seed=3),
	'forest': dict(n=36, r=0.36, h=(0.18, 0.40), w=0.024, bend=0.75, lean=0.55, root=(0.10, 0.18, 0.06), tip=(0.36, 0.52, 0.18), dry=0.20, seed=4),
	'dune':   dict(n=38, r=0.24, h=(0.45, 0.80), w=0.011, bend=0.80, lean=0.22, root=(0.42, 0.44, 0.26), tip=(0.84, 0.82, 0.58), dry=0.55, seed=5),
}
DRY = ((0.40, 0.33, 0.15), (0.88, 0.76, 0.48))
def lin(c): return tuple(x ** 2.2 for x in c)          # sheet colours are sRGB; vertex colours are stored linear
def blade(bm, col, x, y, h, w, ang, lean, bend, rnd, segs):
	dirx, diry = math.cos(ang), math.sin(ang); px, py = -diry, dirx
	twist = rnd.uniform(-0.6, 0.6)
	rows = []
	for k in range(segs + 1):
		t = k / segs
		off = lean * h * t + bend * h * t * t * 0.6          # leaning out and arching over
		z = h * t * (1.0 - 0.25 * bend * t * t)
		cx, cy = x + dirx * off, y + diry * off
		wk = w * (1.0 - t) ** 0.8 if k < segs else 0.0       # tapered to a point
		tw = twist * t; ax, ay = px * math.cos(tw) - dirx * math.sin(tw) * 0.3, py * math.cos(tw) - diry * math.sin(tw) * 0.3
		if k < segs: rows.append((bm.verts.new((cx - ax * wk, cy - ay * wk, z)), bm.verts.new((cx + ax * wk, cy + ay * wk, z)), t))
		else: rows.append((bm.verts.new((cx, cy, z)), None, t))
	faces = []
	for k in range(segs):
		a, b, _ = rows[k]; c, d, _ = rows[k + 1]
		faces.append(bm.faces.new((a, b, d, c)) if d else bm.faces.new((a, b, c)))
	return rows, faces
def clump(name, T, lod):
	rnd = random.Random(T['seed'] * 10 + lod); me = bpy.data.meshes.new(name); bm = bmesh.new()
	ccol = bm.loops.layers.color.new('Color'); uvl = bm.loops.layers.uv.new('UVMap')
	n = T['n'] if lod == 0 else max(8, T['n'] // 3); segs = 4 if lod == 0 else 2
	for i in range(n):
		rr = T['r'] * math.sqrt(rnd.random()); a = rnd.random() * 6.283
		x, y = rr * math.cos(a), rr * math.sin(a)
		h = rnd.uniform(*T['h']) * (1.0 - 0.35 * rr / T['r'])          # taller in the middle of the clump
		w = T['w'] * rnd.uniform(0.8, 1.25) * (1.6 if lod else 1.0)
		ang = a + rnd.uniform(-0.6, 0.6); dry = rnd.random() < T['dry']
		root, tip = (DRY if dry else (T['root'], T['tip']))
		v = rnd.uniform(0.85, 1.12); tipc = tuple(min(1, c * v) for c in tip)
		rows, faces = blade(bm, None, x, y, h, w, ang, T['lean'] * rnd.uniform(0.5, 1.3), T['bend'] * rnd.uniform(0.6, 1.3), rnd, segs)
		for f in faces:
			for l in f.loops:
				t = l.vert.co.z / max(h, 1e-3); c = [root[j] + (tipc[j] - root[j]) * min(1.0, t * 1.15) for j in range(3)]
				l[ccol] = (*c, 1.0)          # byte colour layer: stored as sRGB; l[uvl].uv = (0.5, t)
	bm.to_mesh(me); bm.free()
	ca = me.color_attributes['Color']; me.color_attributes.active_color = ca; me.color_attributes.render_color_index = me.color_attributes.find('Color')
	o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o
bpy.ops.wm.read_factory_settings(use_empty=True)
mat = bpy.data.materials.new('Grass'); mat.use_nodes = True; nt = mat.node_tree; b = nt.nodes['Principled BSDF']
vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'; nt.links.new(vc.outputs['Color'], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.8; mat.use_backface_culling = False
objs = {}
for name, T in TYPES.items():
	for lod in (0, 1):
		o = clump('G_%s_LOD%d' % (name, lod), T, lod); o.data.materials.append(mat); objs[(name, lod)] = o
		o.location = (list(TYPES).index(name) * 1.4, lod * 1.6, 0)
		print(name, lod, len(o.data.polygons) * 2 - sum(1 for p in o.data.polygons if len(p.vertices) == 3), 'tris')
# export with the clumps at the origin, Y up
for o in objs.values(): o.location = (0, 0, 0)
bpy.ops.export_scene.gltf(filepath=OUT + 'grass.glb', export_format='GLB', export_yup=True, export_apply=True, export_vertex_color='ACTIVE')
# ---------------------------------------------------------------- art sheet: each type as a patch on soil, close and from the side
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.render.resolution_x = 900; sc.render.resolution_y = 600; sc.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.68, 0.85, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 4.0; sun.rotation_euler = (math.radians(50), 0, math.radians(35)); sc.collection.objects.link(sun)
soil = bpy.data.materials.new('soil'); soil.use_nodes = True; soil.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.05, 0.035, 0.02, 1)
bpy.ops.mesh.primitive_plane_add(size=3.2); ground = bpy.context.object; ground.data.materials.append(soil)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
for o in objs.values(): o.hide_render = True
for name in TYPES:
	src = objs[(name, 0)]; inst = []
	rnd = random.Random(7)
	for i in range(34):          # a 3 m patch of clumps, as the game scatters them
		c = src.copy(); c.location = (rnd.uniform(-1.3, 1.3), rnd.uniform(-1.3, 1.3), 0); c.rotation_euler = (0, 0, rnd.random() * 6.28); s = rnd.uniform(0.8, 1.2); c.scale = (s, s, s)
		c.hide_render = False; sc.collection.objects.link(c); inst.append(c)
	cam.location = (2.6, -2.6, 1.05); cam.rotation_euler = mathutils.Vector((-2.6, 2.6, -0.8)).to_track_quat('-Z', 'Y').to_euler()
	sc.render.filepath = OUT + 'sheet_%s.png' % name; bpy.ops.render.render(write_still=True)
	for c in inst: bpy.data.objects.remove(c)
print('grass done')
