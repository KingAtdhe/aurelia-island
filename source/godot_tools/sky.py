# physical sky panorama with the game's sun, then clouds from the web game's cloud texture -> sky.png (equirect)
import bpy, math, numpy as np, mathutils
from PIL import Image
W, H = 2048, 1024
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.device = 'CPU'
sc.render.resolution_x = W; sc.render.resolution_y = H
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; nt = w.node_tree
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'; sky.sun_disc = True; sky.sun_size = math.radians(1.2)
d = mathutils.Vector((-0.452, -0.646, 0.616)).normalized()        # towards the sun (Blender axes), from the bake
sky.sun_elevation = math.asin(d.z); sky.sun_rotation = math.atan2(d.x, d.y)
sky.altitude = 200; sky.air_density = 1.0; sky.aerosol_density = 1.2
nt.links.new(sky.outputs[0], nt.nodes['Background'].inputs[0]); nt.nodes['Background'].inputs[1].default_value = 0.08
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'PANO'; cam.data.panorama_type = 'EQUIRECTANGULAR'; cam.rotation_euler = (math.radians(90), 0, 0)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = '/home/claude/bake/sky_raw.png'
bpy.ops.render.render(write_still=True)
img = np.asarray(Image.open('/home/claude/bake/sky_raw.png').convert('RGB')).astype(np.float32) / 255
# clouds: cloud plane at height 1, texture repeats every 1.5 units, fade at the horizon
cl = np.asarray(Image.open('/home/claude/aurelia-island/data/clouds.png').convert('RGBA')).astype(np.float32) / 255
ys, xs = np.mgrid[0:H, 0:W]
lon = (xs + 0.5) / W * 2 * math.pi - math.pi; lat = math.pi / 2 - (ys + 0.5) / H * math.pi
dx = np.cos(lat) * np.sin(lon); dy = np.cos(lat) * np.cos(lon); dz = np.sin(lat)
up = dz > 0.02
u = np.where(up, dx / np.maximum(dz, 0.02), 0) / 5.0; v = np.where(up, dy / np.maximum(dz, 0.02), 0) / 5.0
cs = cl.shape[0]; iu = ((u % 1) * cs).astype(int) % cs; iv = ((v % 1) * cs).astype(int) % cs
a = np.clip((cl[iv, iu, 3] - 0.35) / 0.4, 0, 1) * np.clip((dz - 0.06) / 0.3, 0, 1) * 0.9
sun_dot = np.clip(dx * d.x + dy * d.y + dz * d.z, 0, 1)
ccol = (0.92 + 0.08 * sun_dot[..., None] ** 8) * np.array([1.0, 0.99, 0.97]) * (0.75 + 0.25 * cl[iv, iu, :3].mean(-1)[..., None])
img = img * (1 - a[..., None]) + ccol * a[..., None]
hz = img[H // 2 - 6].mean(0)                                            # below the horizon: hazy sea-level colour, not the dark ground of the sky model
fade = np.clip((H / 2 - ys) / 12.0, 0, 1)[..., None]
low = hz * 0.92 * np.ones_like(img)
img = img * fade + low * (1 - fade)
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save('/home/claude/bake/sky.png')
k = np.unravel_index(np.argmax(np.asarray(Image.open('/home/claude/bake/sky_raw.png').convert('L'))), (H, W)); print('sun pixel', k)
