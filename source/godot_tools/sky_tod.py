# sunset and night skies for the time of day (same layout as sky.py's day sky: 2048 x 1024 equirect, clouds from the web
# game's cloud texture). sunset: physical sky (Blender) with the web game's dusk sun, clouds lit orange from the sun side.
# night: deep blue gradient, stars, the moon, a few dim clouds.   usage: python3 sky_tod.py <out dir>
import sys, math, numpy as np
from PIL import Image
OUT = sys.argv[1]; W, H = 2048, 1024
cl = np.asarray(Image.open('/home/claude/aurelia-island/data/clouds.png').convert('RGBA')).astype(np.float32) / 255
ys, xs = np.mgrid[0:H, 0:W]
lon = (xs + 0.5) / W * 2 * math.pi - math.pi; lat = math.pi / 2 - (ys + 0.5) / H * math.pi
dx = np.cos(lat) * np.sin(lon); dy = np.cos(lat) * np.cos(lon); dz = np.sin(lat)
up = dz > 0.02
u = np.where(up, dx / np.maximum(dz, 0.02), 0) / 5.0; v = np.where(up, dy / np.maximum(dz, 0.02), 0) / 5.0
cs = cl.shape[0]; iu = ((u % 1) * cs).astype(int) % cs; iv = ((v % 1) * cs).astype(int) % cs
camt = np.clip((cl[iv, iu, 3] - 0.35) / 0.4, 0, 1) * np.clip((dz - 0.06) / 0.3, 0, 1)
cshade = (0.75 + 0.25 * cl[iv, iu, :3].mean(-1))
def horizon(img, k=0.92):
    hz = img[H // 2 - 6].mean(0); fade = np.clip((H / 2 - ys) / 12.0, 0, 1)[..., None]
    return img * fade + hz * k * (1 - fade)
def save(img, name): Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save('%s/%s' % (OUT, name)); print(name)

# ---- sunset
import bpy, mathutils
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.device = 'CPU'
sc.render.resolution_x = W; sc.render.resolution_y = H
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; nt = w.node_tree
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'; sky.sun_disc = True; sky.sun_size = math.radians(1.6)
d = mathutils.Vector((-0.72, -0.66, 0.2)).normalized()          # the web game's SUN_DUSK (x, -z, y)
d = mathutils.Vector((d.x, d.y, 0.075)).normalized()               # a little lower: a proper sunset glow
sky.sun_elevation = math.asin(d.z); sky.sun_rotation = math.atan2(d.x, d.y)
sky.altitude = 200; sky.air_density = 1.4; sky.aerosol_density = 2.2
nt.links.new(sky.outputs[0], nt.nodes['Background'].inputs[0]); nt.nodes['Background'].inputs[1].default_value = 0.16
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'PANO'; cam.data.panorama_type = 'EQUIRECTANGULAR'; cam.rotation_euler = (math.radians(90), 0, 0)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = '/home/claude/bake/sky_sunset_raw.png'
bpy.ops.render.render(write_still=True)
img = np.asarray(Image.open('/home/claude/bake/sky_sunset_raw.png').convert('RGB')).astype(np.float32) / 255
sd = np.clip(dx * d.x + dy * d.y + dz * d.z, 0, 1)
orange = np.array([1.0, 0.48, 0.18])
img = img + (sd ** 6 * 0.42 + (1 - np.clip(dz, 0, 1)) ** 10 * (0.12 + 0.3 * sd ** 2))[..., None] * orange * up[..., None]   # glow round the sun and along the horizon
img = img * np.array([1.0, 0.93, 0.9])
lit = np.array([1.08, 0.58, 0.30]); shade = np.array([0.34, 0.28, 0.38])
ccol = (shade + (lit - shade) * (0.25 + 0.75 * sd[..., None] ** 3)) * cshade[..., None]
a = camt * 0.85
img = img * (1 - a[..., None]) + ccol * a[..., None]
save(horizon(img, 0.95), 'sky_sunset.png')

# ---- night
t = np.clip(dz, 0, 1)[..., None]
zen = np.array([0.010, 0.016, 0.040]); hor = np.array([0.055, 0.075, 0.115])
img = hor + (zen - hor) * np.sqrt(t)
rng = np.random.default_rng(3); n = 5200
sx = rng.integers(0, W, n); sy = rng.integers(0, H // 2 - 20, n); br = rng.random(n) ** 3 * 0.85 + 0.12
fade_s = np.clip((H / 2 - sy) / 160.0, 0, 1)
for k in range(n):
    c = br[k] * fade_s[k] * np.array([0.95, 0.97, 1.0]) if rng.random() < 0.8 else br[k] * fade_s[k] * np.array([1.0, 0.9, 0.75])
    img[sy[k], sx[k]] = np.maximum(img[sy[k], sx[k]], c)
    if br[k] > 0.6: img[sy[k], (sx[k] + 1) % W] = np.maximum(img[sy[k], (sx[k] + 1) % W], c * 0.5); img[sy[k] + 1, sx[k]] = np.maximum(img[sy[k] + 1, sx[k]], c * 0.5)
md = np.array([0.55, 0.45, 0.70]); md /= np.linalg.norm(md)       # the moon, high in the south-east
mdot = dx * md[0] + dy * md[1] + dz * md[2]
moon = np.clip((mdot - math.cos(math.radians(1.3))) / 0.00004, 0, 1)
halo = np.clip(mdot, 0, 1) ** 400 * 0.25
img = img + halo[..., None] * np.array([0.7, 0.78, 0.95]) + moon[..., None] * np.array([0.95, 0.93, 0.86])
ccol = np.array([0.03, 0.036, 0.055]) * cshade[..., None] + (np.clip(mdot, 0, 1) ** 20 * 0.12)[..., None]
a = camt * 0.7 * (1 - np.clip(mdot, 0, 1) ** 60)          # clear sky round the moon
img = img * (1 - a[..., None]) + ccol * a[..., None]
save(horizon(img, 1.0), 'sky_night.png')
