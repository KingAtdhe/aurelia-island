# Impostor atlas for distant trees, rendered from the game's own tree models (godot/assets/island/flora_*.glb): 4 x 2 cells of
# 512 px, same layout as the web game's atlas (0 spruce, 1 spruce_b / pine, 2 broadleaf, 3 snowy spruce, 4 birch, 5 palm,
# 6 conifer from above, 7 broadleaf from above). Side cells are squeezed to the card's width/height ratio (ASP) so they unstretch
# on the card. Colour = the model's albedo (texture x vertex colour), alpha cut-out; the game's card shader lights it.
import bpy, os, sys, math, numpy as np
A = '/home/claude/aurelia-island/godot/assets/island/'; OUT = '/home/claude/cards/'
ASP = [0.66, 0.66, 1.3, 0.5, 1.0, 0.9]
CELLS = [('spruce', 'side'), ('spruce_b', 'side'), ('tree_t_oak', 'side'), ('spruce_snow', 'side'), ('birch', 'side'), ('palm', 'side'), ('spruce', 'top'), ('tree_t_oak', 'top')]
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in ('flora_flora', 'flora_kit', 'flora_tprops'): bpy.ops.import_scene.gltf(filepath=A + f + '.glb')
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = False; sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.cycles.max_bounces = 2; sc.cycles.transparent_max_bounces = 16
# every material: emit its albedo (texture x vertex colour where the mesh has one), keep the alpha cut-out
with_col = {m for o in bpy.data.objects if o.type == 'MESH' and len(o.data.color_attributes) for m in o.data.materials}
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt = m.node_tree; b = next((x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'), None)
    if not b: continue
    out = next(x for x in nt.nodes if x.type == 'OUTPUT_MATERIAL')
    col = b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].links else None
    alpha = b.inputs['Alpha'].links[0].from_socket if b.inputs['Alpha'].links else None
    attr = nt.nodes.new('ShaderNodeVertexColor'); attr.layer_name = 'Color'
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    if col: nt.links.new(col, mul.inputs['A'])
    else: mul.inputs['A'].default_value = b.inputs['Base Color'].default_value
    if m in with_col: nt.links.new(attr.outputs['Color'], mul.inputs['B'])
    else: mul.inputs['B'].default_value = (1, 1, 1, 1)
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(mul.outputs['Result'], em.inputs['Color'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mix = nt.nodes.new('ShaderNodeMixShader')
    if alpha:
        gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.4; nt.links.new(alpha, gt.inputs[0]); nt.links.new(gt.outputs[0], mix.inputs[0])
    else: mix.inputs[0].default_value = 1.0
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs['Surface'])
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True; world.node_tree.nodes['Background'].inputs[1].default_value = 0.0
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
roots = {o.name: o for o in bpy.data.objects if o.name.startswith('S_')}
def tree(name):
    r = roots['S_%s_LOD0' % name]; objs = [r] + list(r.children_recursive)
    pts = [o.matrix_world @ __import__('mathutils').Vector(c) for o in objs if o.type == 'MESH' for c in o.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
    return objs, lo, hi
from PIL import Image
atlas = Image.new('RGBA', (2048, 1024), (0, 0, 0, 0))
for q, (name, view) in enumerate(CELLS):
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = True
    objs, lo, hi = tree(name)
    for o in objs: o.hide_render = False
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2; h = hi[2] - lo[2]; wid = max(hi[0] - lo[0], hi[1] - lo[1])
    if view == 'side':
        asp = ASP[q]; sc.render.resolution_x = int(round(512 * asp)) if asp < 1 else 512; sc.render.resolution_y = 512 if asp < 1 else int(round(512 / asp))
        cam.data.ortho_scale = max(h, h * asp)          # the card is h tall and h * asp wide, base at the bottom
        cam.location = (cx, cy - 100, lo[2] + h / 2); cam.rotation_euler = (math.pi / 2, 0, 0)
    else:
        sc.render.resolution_x = sc.render.resolution_y = 512; cam.data.ortho_scale = wid * 1.02
        cam.location = (cx, cy, hi[2] + 50); cam.rotation_euler = (0, 0, 0)
    sc.render.filepath = OUT + 'cell_%d.png' % q; bpy.ops.render.render(write_still=True)
    im = Image.open(OUT + 'cell_%d.png' % q).convert('RGBA').resize((512, 512), Image.LANCZOS)
    atlas.paste(im, ((q % 4) * 512, (q // 4) * 512))
# bleed the colour out under transparent pixels so mip-maps do not darken the edges
a = np.array(atlas).astype(np.float32); m = a[:, :, 3] > 100
from scipy import ndimage
idx = ndimage.distance_transform_edt(~m, return_distances=False, return_indices=True)
a[~m, :3] = a[idx[0][~m], idx[1][~m], :3]
Image.fromarray(a.clip(0, 255).astype(np.uint8)).save(OUT + 'tree_cards.png')
print('cards done')
