"""Street life for Aurelia Island: clutter props (scooters, bicycle racks, cafe tables with parasols, flower planters, a news kiosk),
people (standing and two walking poses, several outfits) and traffic cars (the Aurelia low-detail bodies, painted white so the
instance colour gives each car its paint). All are props placed as instances; the game moves the traffic and the walkers."""
import math
import numpy as np
import bmesh
import isle_props as P
from isle_props import bbox, lathe, sweep, prism


def scooter(K, M):
    for x in (-0.55, 0.55):
        t = lathe([(0.0, -0.05), (0.2, -0.05), (0.2, 0.05), (0.0, 0.05)], 14)
        for v in t.verts: a, b, c = v.co; v.co = (x + a, c, 0.2 + b)
        K.obj(t, M['plastic'], (0.08, 0.08, 0.08), 'box', 0.5)
    K.obj(bbox(0.0, 0, 0.35, 1.0, 0.36, 0.16), M['smooth'], (1, 1, 1), 'box', 1.0, 0.04, 2)                 # deck (paint via tint)
    K.obj(bbox(-0.35, 0, 0.62, 0.55, 0.34, 0.32), M['smooth'], (1, 1, 1), 'box', 1.0, 0.06, 2)               # body
    K.obj(bbox(-0.3, 0, 0.82, 0.6, 0.3, 0.1), M['plastic'], (0.1, 0.1, 0.1), 'box', 1.0, 0.04, 2)            # seat
    K.obj(sweep([(0.5, 0, 0.35), (0.6, 0, 0.9), (0.55, 0, 1.05)], 0.035, 8), M['galv'], (0.6, 0.6, 0.6))
    K.obj(bbox(0.55, 0, 1.05, 0.06, 0.6, 0.05), M['plastic'], (0.1, 0.1, 0.1))
    K.obj(bbox(0.62, 0, 0.82, 0.12, 0.3, 0.32), M['smooth'], (1, 1, 1), 'box', 1.0, 0.03, 1)
    K.obj(bbox(0.69, 0, 0.88, 0.02, 0.16, 0.1), M['lens'], (1.0, 0.96, 0.85))


def bikerack(K, M):
    for y in np.linspace(-1.6, 1.6, 5):
        K.obj(sweep([(-0.35, y, 0.0), (-0.35, y, 0.65), (-0.2, y, 0.8), (0.2, y, 0.8), (0.35, y, 0.65), (0.35, y, 0.0)], 0.025, 6), M['galv'], (0.7, 0.7, 0.72))
    for y, c in ((-0.8, (0.15, 0.3, 0.6)), (0.8, (0.6, 0.12, 0.1))):                           # two parked bicycles
        for x in (-0.55, 0.55):
            w = lathe([(0.33, -0.015), (0.35, 0.0), (0.33, 0.015)], 20, close_top=False, close_bottom=False)
            for v in w.verts: a, b, cz = v.co; v.co = (x + a, y + 0.12 + cz, 0.35 + b)
            K.obj(w, M['plastic'], (0.06, 0.06, 0.06))
        K.obj(sweep([(-0.55, y + 0.12, 0.35), (-0.05, y + 0.12, 0.35), (0.35, y + 0.12, 0.72), (-0.2, y + 0.12, 0.72), (-0.05, y + 0.12, 0.35)], 0.02, 5), M['smooth'], c)
        K.obj(sweep([(0.55, y + 0.12, 0.35), (0.38, y + 0.12, 0.8), (0.36, y + 0.12, 0.95)], 0.02, 5), M['smooth'], c)
        K.obj(bbox(-0.22, y + 0.12, 0.8, 0.22, 0.08, 0.04), M['plastic'], (0.1, 0.1, 0.1))


def cafe_set(K, M):
    K.obj(lathe([(0.03, 0.0), (0.03, 2.3), (0.0, 2.32)], 8), M['galv'], (0.8, 0.8, 0.8))
    K.obj(lathe([(1.4, 1.95), (0.0, 2.35)], 16, close_bottom=True), M['fabric'], (0.95, 0.93, 0.88), smooth=False)   # parasol
    K.obj(lathe([(0.0, 0.0), (0.25, 0.0), (0.03, 0.05), (0.03, 0.72), (0.35, 0.72), (0.35, 0.75), (0.0, 0.75)], 16), M['iron'], (0.2, 0.2, 0.22))
    for k in range(3):
        a = k * 2.1; cx, cy = 0.7 * math.cos(a), 0.7 * math.sin(a)
        for dx, dy in ((-0.18, -0.18), (0.18, -0.18), (-0.18, 0.18), (0.18, 0.18)):
            K.obj(bbox(cx + dx, cy + dy, 0.22, 0.03, 0.03, 0.44), M['iron'], (0.2, 0.2, 0.22))
        K.obj(bbox(cx, cy, 0.46, 0.42, 0.42, 0.04), M['wood'], (0.85, 0.7, 0.55), 'box', 0.5)
        bx, by = cx + 0.2 * math.cos(a), cy + 0.2 * math.sin(a)
        K.obj(bbox(bx, by, 0.7, 0.04, 0.4, 0.4, a), M['wood'], (0.85, 0.7, 0.55), 'box', 0.5)


def planter(K, M):
    K.obj(bbox(0, 0, 0.3, 1.6, 0.7, 0.6), M['concrete'], (0.85, 0.84, 0.8), 'box', 1.0, 0.03, 2)
    K.obj(bbox(0, 0, 0.58, 1.45, 0.55, 0.06), M['concrete'], (0.3, 0.22, 0.16))
    rng = np.random.default_rng(4)
    for k in range(10):
        x, y = rng.uniform(-0.6, 0.6), rng.uniform(-0.2, 0.2); c = [(0.85, 0.15, 0.2), (0.95, 0.75, 0.2), (0.6, 0.3, 0.75), (0.95, 0.95, 0.9)][k % 4]
        K.obj(lathe([(0.0, 0.0), (0.12, 0.06), (0.1, 0.16), (0.0, 0.2)], 6, x, y, 0.6), M['plastic'], (0.2, 0.45, 0.15))
        K.obj(lathe([(0.0, 0.0), (0.07, 0.03), (0.0, 0.06)], 6, x, y, 0.78), M['smooth'], c)


def news_kiosk(K, M):
    K.obj(bbox(0, 0, 1.3, 1.8, 2.4, 2.6), M['smooth'], (0.18, 0.32, 0.25), 'box', 1.0, 0.04, 2)
    K.obj(bbox(0.92, 0, 1.5, 0.04, 2.0, 1.2), M['winglass'], (1, 1, 1))
    K.obj(bbox(1.2, 0, 2.7, 1.0, 2.8, 0.08), M['smooth'], (0.18, 0.32, 0.25), 'box', 1.0, 0.02, 1)
    K.obj(bbox(1.0, 0, 0.95, 0.4, 2.2, 0.06), M['wood'], (0.8, 0.65, 0.5))
    F = __import__('isle_houses').Frame((0.95, 0, 0), (0, 1, 0), (1, 0, 0))
    K.obj(F.box(-1.0, 1.0, 0.0, 0.02, 2.2, 2.6), M['shops'], (1, 1, 1), 'sign', 1.0, sign=P.sign_cell_uv_frame(F, 15, 0.0, 2.4, 2.0, 0.4))


def newsboxes(K, M):
    for k, c in enumerate(((0.75, 0.12, 0.1), (0.15, 0.35, 0.65), (0.9, 0.75, 0.15))):
        y = (k - 1) * 0.55
        K.obj(bbox(0, y, 0.55, 0.45, 0.5, 0.5), M['smooth'], c, 'box', 1.0, 0.02, 1)
        K.obj(bbox(0.23, y, 0.75, 0.02, 0.36, 0.22), M['winglass'], (1, 1, 1))
        K.obj(lathe([(0.21, 0.0), (0.21, 0.02), (0.0, 0.02)], 12, 0, y, 0.8), M['smooth'], c)
        for dy in (-0.18, 0.18): K.obj(bbox(0, y + dy, 0.15, 0.05, 0.05, 0.3), M['iron'], (0.2, 0.2, 0.2))


def trash_bags(K, M):
    rng = np.random.default_rng(9)
    for k in range(5):
        x, y, r = rng.uniform(-0.6, 0.6), rng.uniform(-0.4, 0.4), rng.uniform(0.26, 0.36)
        t = lathe([(0.0, 0.0), (r * 0.8, 0.02), (r, r * 0.6), (r * 0.85, r * 1.3), (0.08, r * 1.6), (0.04, r * 1.85), (0.0, r * 1.9)], 10, x, y, 0.0)
        for v in t.verts: v.co.x += math.sin(v.co.z * 7 + k) * 0.03; v.co.y += math.cos(v.co.z * 5 + k) * 0.03
        K.obj(t, M['plastic'], (0.05, 0.05, 0.06) if k % 3 else (0.15, 0.25, 0.12), 'box', 1.0, smooth=True)


def cones(K, M):
    for x, y in ((0.0, 0.0), (1.4, 0.2), (2.8, -0.1)):
        K.obj(bbox(x, y, 0.02, 0.42, 0.42, 0.04), M['plastic'], (0.1, 0.1, 0.1))
        K.obj(lathe([(0.15, 0.04), (0.04, 0.72), (0.0, 0.73)], 12, x, y, 0.0), M['smooth'], (0.98, 0.36, 0.06), smooth=True)
        K.obj(lathe([(0.117, 0.3), (0.088, 0.48)], 12, x, y, 0.0, close_bottom=False, close_top=False), M['smooth'], (0.95, 0.95, 0.95))


def phone_booth(K, M):
    K.obj(bbox(0, 0, 1.25, 1.0, 1.0, 2.5), M['smooth'], (0.1, 0.25, 0.45), 'box', 1.0, 0.03, 2)
    for F in __import__('isle_city').fronts(1.0, 1.0)[:3]:
        K.obj(F[0].box(-0.38, 0.38, 0.0, 0.02, 0.3, 2.2), M['winglass'], (1, 1, 1))
    K.obj(bbox(0, 0, 2.58, 1.06, 1.06, 0.16), M['lens'], (0.95, 0.97, 1.0))
    K.obj(bbox(0, 0, 2.7, 1.1, 1.1, 0.08), M['smooth'], (0.1, 0.25, 0.45))


def mailbox(K, M):
    K.obj(bbox(0, 0, 0.45, 0.12, 0.12, 0.9), M['iron'], (0.15, 0.15, 0.15))
    K.obj(bbox(0, 0, 1.05, 0.45, 0.5, 0.5), M['smooth'], (0.95, 0.75, 0.1), 'box', 1.0, 0.04, 2)
    K.obj(lathe([(0.25, 0.0), (0.25, 0.45), (0.0, 0.45)], 14), M['smooth'], (0.95, 0.75, 0.1)) if False else None
    K.obj(bbox(0.235, 0, 1.15, 0.02, 0.3, 0.05), M['iron'], (0.1, 0.1, 0.1))


SKIN = [(0.93, 0.76, 0.62), (0.78, 0.56, 0.42), (0.55, 0.38, 0.27), (0.98, 0.84, 0.72)]
OUTFIT = [((0.2, 0.3, 0.55), (0.15, 0.15, 0.18)), ((0.75, 0.2, 0.18), (0.3, 0.32, 0.4)), ((0.92, 0.9, 0.85), (0.2, 0.22, 0.3)), ((0.25, 0.45, 0.3), (0.55, 0.45, 0.35)), ((0.85, 0.7, 0.25), (0.2, 0.2, 0.22)), ((0.35, 0.3, 0.5), (0.6, 0.58, 0.55))]


def person(K, M, outfit=0, pose='stand'):
    """Stylised person 1.75 m, facing +X. pose: stand, walk_a, walk_b."""
    top, legs = OUTFIT[outfit % len(OUTFIT)]; skin = SKIN[outfit % 4]; hair = [(0.12, 0.08, 0.05), (0.35, 0.22, 0.1), (0.05, 0.05, 0.05), (0.6, 0.45, 0.25)][outfit % 4]
    sw = {'stand': 0.0, 'walk_a': 0.38, 'walk_b': -0.38, 'walk_c': 0.2, 'walk_d': -0.2}[pose]
    for sg in (-1, 1):                                                                        # legs and shoes
        a = sw * sg; hip = np.array([0.0, sg * 0.1, 0.92]); knee = hip + np.array([0.45 * math.sin(a), 0, -0.45 * math.cos(a)]); foot = knee + np.array([0.45 * math.sin(a * 0.6), 0, -0.45 * math.cos(a * 0.6)])
        K.obj(sweep([tuple(hip), tuple(knee), tuple(foot + (0, 0, 0.06))], lambda u: 0.085 - 0.03 * u, 8), M['fabric'], legs, 'box', 0.5)
        K.obj(bbox(foot[0] + 0.06, foot[1], 0.05, 0.26, 0.1, 0.1), M['plastic'], (0.1, 0.09, 0.08), 'box', 0.5, 0.03, 2)
    tor = lathe([(0.0, 0.86), (0.16, 0.88), (0.17, 1.0), (0.15, 1.12), (0.17, 1.28), (0.2, 1.4), (0.13, 1.49), (0.0, 1.5)], 14)
    for v in tor.verts: v.co.x *= 0.62                                                             # flatter front to back
    K.obj(tor, M['fabric'], top, 'cyl', 0.6)   # torso
    K.obj(lathe([(0.05, 1.48), (0.05, 1.56)], 8, close_top=False), M['smooth'], skin)
    K.obj(lathe([(0.0, 1.55), (0.08, 1.57), (0.1, 1.64), (0.095, 1.72), (0.06, 1.78), (0.0, 1.79)], 12), M['smooth'], skin)                         # head
    K.obj(lathe([(0.1, 1.66), (0.105, 1.73), (0.07, 1.8), (0.0, 1.81)], 12, -0.012, 0, 0), M['fabric'], hair)
    for sg in (-1, 1):                                                                        # arms swing opposite to the legs
        a = -sw * sg * 0.8; sh = np.array([0.0, sg * 0.205, 1.43]); el = sh + np.array([0.28 * math.sin(a), sg * 0.03, -0.28 * math.cos(a)]); wr = el + np.array([0.27 * math.sin(a * 1.2 + 0.2), 0, -0.27 * math.cos(a * 1.2)])
        K.obj(sweep([tuple(sh), tuple(el), tuple(wr)], lambda u: 0.055 - 0.015 * u, 6), M['fabric'], top, 'box', 0.5)
        K.obj(lathe([(0.0, -0.05), (0.045, -0.02), (0.04, 0.04), (0.0, 0.06)], 6, wr[0], wr[1], wr[2] - 0.04), M['smooth'], skin)


def traffic_car2(K, M, kind):
    """Modelled traffic car (isle_traffic): subdivided body, cabin glass, arches, bumpers, lights, spoked wheels."""
    import isle_traffic as TR
    for bm, ci in TR.build(kind, 1 if P.LOD else 0):
        c = TR.COLOURS[ci]
        if ci == TR.PAINT: K.obj(bm, M['smooth'], (0.95, 0.95, 0.95), 'box', 1.0, 0.0, smooth=True, angle=60)
        elif ci == TR.GLASS: K.obj(bm, M['winglass'], (1, 1, 1), 'box', 1.0, 0.0, smooth=True, angle=60)
        elif ci in (TR.LAMP_F, TR.LAMP_R, TR.AMBER): K.obj(bm, M['lens'], c, 'box', 1.0, 0.0)
        elif ci == TR.TYRE: K.obj(bm, M['plastic'], (0.05, 0.05, 0.055), 'box', 1.0, 0.0, smooth=True, angle=50)
        elif ci in (TR.RIM, TR.CHROME): K.obj(bm, M['galv'], c, 'box', 1.0, 0.0, smooth=True, angle=50)          # not tinted by the paint colour
        elif ci == TR.PLATE: K.obj(bm, M['plaster'], (1.0, 1.0, 0.95), 'box', 1.0, 0.0)
        else: K.obj(bm, M['smooth'], c, 'box', 1.0, 0.0, smooth=ci == TR.BLACK, angle=50)


def traffic_car(K, M, kind):
    import isle_car as CAR
    V, F, C = CAR.low_mesh(kind, (0.999, 0.999, 0.999), 0.42, 0.36)
    cols, inv = np.unique(np.round(C, 3), axis=0, return_inverse=True); inv = inv.ravel()
    for ci, c in enumerate(cols):
        fsel = F[(inv[F] == ci).all(1)]
        if not len(fsel): continue
        bm = bmesh.new(); vs = [bm.verts.new(tuple(v)) for v in V]
        for f in fsel:
            try: bm.faces.new([vs[i] for i in f])
            except ValueError: pass
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        paint = c.min() > 0.99; mat = M['smooth'] if paint or c.max() < 0.1 else (M['winglass'] if c.max() < 0.2 else M['smooth'])
        K.obj(bm, mat, (0.95, 0.95, 0.95) if paint else tuple(c), 'box', 1.0, 0.0, smooth=True, angle=50)


def register():
    D = dict(scooter=(scooter, {}), bikerack=(bikerack, {}), cafe=(cafe_set, {}), planter=(planter, {}), kiosk=(news_kiosk, {}), newsbox=(newsboxes, {}), trashbags=(trash_bags, {}), cones=(cones, {}), phonebooth=(phone_booth, {}), mailbox=(mailbox, {}),
             tcar_a=(lambda K, M: traffic_car2(K, M, 'hatch'), {}), tcar_b=(lambda K, M: traffic_car2(K, M, 'sedan'), {}), tcar_c=(lambda K, M: traffic_car2(K, M, 'van'), {}), tcar_d=(lambda K, M: traffic_car2(K, M, 'suv'), {}), tcar_e=(lambda K, M: traffic_car2(K, M, 'taxi'), {}))
    for o in range(4): D['person_%d' % o] = (lambda K, M, o=o: person(K, M, o, 'stand'), {})
    for o in range(4):
        for ps in ('walk_a', 'walk_b', 'stand', 'walk_c', 'walk_d'): D['walker_%d_%s' % (o, {'walk_a': 'a', 'walk_b': 'b', 'stand': 'm', 'walk_c': 'c', 'walk_d': 'd'}[ps])] = (lambda K, M, o=o, ps=ps: person(K, M, o, ps), {})
    for k, v in D.items(): P.PROPS[k] = v; P.HEIGHT[k] = 1.8
