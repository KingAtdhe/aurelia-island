"""Building texturing: classify faces into parts, build per-part materials, bake.
usage: python3 bld.py -- cafe [debug]"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, bpy, math
from tlib import *

args = sys.argv[sys.argv.index('--') + 1:]
which = args[0]; debug = 'debug' in args

DBG = {'wall': (0.9, 0.9, 0.85), 'roof': (0.8, 0.35, 0.2), 'wood': (0.2, 0.4, 0.9), 'awning': (0.9, 0.1, 0.1),
       'metal': (0.1, 0.5, 0.2), 'pot': (0.7, 0.4, 0.3), 'leaf': (0.2, 0.8, 0.1), 'glass': (0.05, 0.05, 0.1),
       'door': (0.5, 0.3, 0.1), 'iron': (0.1, 0.1, 0.1), 'step': (0.9, 0.8, 0.5), 'stone': (0.5, 0.5, 0.5),
       'hay': (0.95, 0.85, 0.3), 'red': (0.8, 0.1, 0.1), 'frame': (1, 1, 1), 'cap': (0.7, 0.6, 0.4),
       'road': (0.2, 0.2, 0.2), 'floor': (0.6, 0.6, 0.6), 'kerb': (0.4, 0.4, 0.45), 'alu': (0.7, 0.7, 0.8),
       'pump': (0.95, 0.95, 0.9), 'canopy': (1, 1, 1), 'bark': (0.4, 0.25, 0.1), 'needle': (0.1, 0.5, 0.1),
       'misc': (1, 0, 1), 'plinth': (0.6, 0.55, 0.4), 'trim': (0.45, 0.3, 0.2), 'grass': (0.5, 0.7, 0.2), 'tower': (0.95, 0.95, 0.95), 'cottage': (0.85, 0.85, 0.75), 'croof': (0.8, 0.4, 0.2), 'fascia': (0.1, 0.5, 0.3), 'pumptop': (0.1, 0.6, 0.4)}


def ctx(o):
    c, n, ar = face_data(o); fid, boxes = islands(o); fid = np.array(fid)
    isl_area = np.bincount(fid, weights=ar)
    main = int(np.argmax(isl_area))
    bmin = np.array([b[0] for b in boxes]); bmax = np.array([b[1] for b in boxes])
    return c, n, ar, fid, bmin, bmax, main, isl_area


def per_island(fid, sel_isl):
    return np.isin(fid, np.where(sel_isl)[0])


def debug_render(o, cls, name):
    names = sorted(set(cls))
    o.data.materials.clear()
    for k in names:
        m = bpy.data.materials.new(k); m.diffuse_color = DBG.get(k, (1, 0, 1)) + (1,); o.data.materials.append(m)
    o.data.polygons.foreach_set('material_index', np.array([names.index(k) for k in cls], dtype=np.int32))
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
    sc.render.resolution_x = 900; sc.render.resolution_y = 700
    cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
    co = np.array([v.co[:] for v in o.data.vertices]); mn, mx = co.min(0), co.max(0)
    from mathutils import Vector
    ctr = Vector(((mn + mx) / 2).tolist()); R = float(np.linalg.norm(mx - mn)) / 2
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = R * 2.1
    for k, az in enumerate((-60, 120)):
        a = math.radians(az); e = math.radians(22)
        cam.location = ctr + Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * R * 4
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'/home/claude/tripo/dbg_{name}_{k}.png'; bpy.ops.render.render(write_still=True)


TREE_KW = {}
LO = {'bld_cafe': 5200, 'bld_house': 5000, 'bld_barn': 5200, 'bld_lighthouse': 6500, 'bld_petrol': 5200, 'bld_bridge': 5000, 'tree_pine': 5000}
def build(o, cls, recipes, name, res=2048, **kw):
    names = [k for k in recipes if k in set(cls)]
    missing = set(cls) - set(names)
    assert not missing, missing
    mats = [recipes[k]() for k in names]
    assign(o, mats, [names.index(k) for k in cls])
    bake(o, name, res=res, lo_tris=LO.get(name), extr=0.06, **kw)


# ---------------------------------------------------------------- CAFE
def cafe():
    o = load('mediterranean_roadside_cafe', scale=7.5)
    c, n, ar, fid, bmin, bmax, main, ia = ctx(o)
    cls = np.array(['wood'] * len(c), dtype=object)
    xc = (bmin[:, 0] + bmax[:, 0]) / 2
    yc = (bmin[:, 1] + bmax[:, 1]) / 2
    ext = bmax - bmin
    pot_i = (bmin[:, 2] < 0.06) & (bmax[:, 2] > 0.25) & (bmax[:, 2] < 0.75) & (ext[:, 0] > 0.25) & (np.abs(ext[:, 0] - ext[:, 1]) < 0.12)
    plant_i = pot_i.copy()
    for i in np.where(pot_i)[0]:
        d = np.hypot(xc - xc[i], yc - yc[i])
        plant_i |= (d < 0.75) & (bmin[:, 2] > 0.2) & (bmax[:, 2] < 2.4) & (ext.max(1) < 1.3) & (bmin[:, 2] < 1.6)
    furn_i = (bmax[:, 2] < 1.4) & ((bmin[:, 1] + bmax[:, 1]) / 2 < -2.55) & ~plant_i
    awn_i = (bmin[:, 2] > 2.15) & (bmax[:, 2] < 3.4) & ((bmax[:, 0] - bmin[:, 0]) + (bmax[:, 1] - bmin[:, 1]) > 1.2)
    roof_i = (bmin[:, 2] > 2.5) & ~awn_i
    P = per_island
    cls[P(fid, furn_i)] = 'metal'
    cls[P(fid, awn_i)] = 'awning'
    cls[P(fid, roof_i)] = 'roof'
    pl = P(fid, plant_i)
    cls[pl & (c[:, 2] < 0.55)] = 'pot'; cls[pl & (c[:, 2] >= 0.55)] = 'leaf'
    m = fid == main
    cls[m] = 'wall'
    cls[m & (c[:, 2] > 2.62) & (n[:, 2] > 0.55)] = 'roof'
    cls[m & (c[:, 2] > 2.75) & (np.abs(n[:, 2]) < 0.2) & (c[:, 2] < 3.0)] = 'roof'
    cls[m & (c[:, 2] > 4.7)] = 'roof'
    cls[(cls == 'roof') & (np.abs(n[:, 2]) < 0.3) & (c[:, 2] < 4.4) & (ar > 0.05)] = 'wall'
    # glass: large outward faces of window islands
    win_i = (bmin[:, 2] > 0.8) & (bmax[:, 2] < 2.4) & ~plant_i & ~furn_i
    cls[P(fid, win_i) & (ar > 0.05) & (np.abs(n[:, 2]) < 0.3)] = 'glass'
    return o, cls

def cafe_recipes():
    def wall():
        m = M('wall'); return m.out(m.tex('cafe_plaster', (2.0, 2.0, 2.4), blend=0.2), bump=0.2)
    def roof():
        m = M('roof'); return m.out(m.tex('roof_terracotta', 1.6, blend=0.3), bump=0.5)
    def wood():
        m = M('wood'); return m.out(m.tex('shutters', 0.9), bump=0.3)
    def awning():
        m = M('awning'); return m.out(m.tex('cafe_awning', 1.0, blend=0.4), bump=0.1)
    def metal():
        m = M('metal'); return m.out(m.tex('cafe_metal', 0.4), rough=0.5, bump=0.1)
    def pot():
        m = M('pot'); return m.out(m.tint(m.tex('roof_terracotta', 0.3), (1.0, 0.9, 0.85)), bump=0.1)
    def leaf():
        m = M('leaf'); return m.out(m.hue(m.tex('boulder_moss', 0.3), 0.5, 1.1, 0.9), bump=0.1)
    def glass():
        m = M('glass'); return m.out(m.rgb((0.05, 0.07, 0.08)), rough=0.1, bump=0)
    return dict(wall=wall, roof=roof, wood=wood, awning=awning, metal=metal, pot=pot, leaf=leaf, glass=glass)



def plants(c, fid, bmin, bmax, cls, zpot=None):
    """detect pots (round, 0.25-0.75 m tall, on ground or sill) and the leaf islands around them"""
    xc = (bmin[:, 0] + bmax[:, 0]) / 2; yc = (bmin[:, 1] + bmax[:, 1]) / 2; ext = bmax - bmin
    pot_i = (bmin[:, 2] < 0.2) & (ext[:, 2] > 0.25) & (ext[:, 2] < 0.9) & (ext[:, 0] > 0.2) & (ext[:, 0] < 0.8) & (np.abs(ext[:, 0] - ext[:, 1]) < 0.15)
    plant_i = pot_i.copy()
    for i in np.where(pot_i)[0]:
        d = np.hypot(xc - xc[i], yc - yc[i])
        plant_i |= (d < 0.75) & (bmin[:, 2] > bmax[i, 2] - 0.3) & (bmax[:, 2] < 2.4) & (ext.max(1) < 1.3) & (bmin[:, 2] < 1.6)
    pl = per_island(fid, plant_i)
    top = {i: bmax[i, 2] for i in np.where(pot_i)[0]}
    potf = per_island(fid, pot_i)
    cls[pl & ~potf] = 'leaf'; cls[potf] = 'pot'
    return plant_i


def house():
    o = load('mediterranean_village_house', scale=8.5)
    c, n, ar, fid, bmin, bmax, main, ia = ctx(o)
    ext = bmax - bmin; es = np.sort(ext, 1)
    P = per_island
    cls = np.array(['door'] * len(c), dtype=object)            # default: dark wood trims
    flat_i = np.array([(np.abs(n[fid == i, 2]) > 0.6).mean() for i in range(len(ext))])
    cls[P(fid, (ext[:, 2] > 0.6) & (ext[:, 2] < 1.6) & (es[:, 0] < 0.25))] = 'wood'   # shutters / window frames
    cls[P(fid, (ext[:, 2] < 0.4) & (flat_i > 0.35) & (es[:, 1] > 0.25))] = 'step'        # stairs, sills, balcony slab
    cls[P(fid, (es[:, 1] < 0.12) & (es[:, 2] > 0.3) & (bmin[:, 2] > 2.0) & (bmax[:, 2] < 6.0))] = 'iron'  # railing bars
    rail = (bmin[:, 2] > 3.0) & (bmax[:, 2] < 4.4) & (ext[:, 2] < 0.15) & (es[:, 2] > 1.0) & (flat_i < 0.6)
    cls[P(fid, rail)] = 'iron'
    cls[P(fid, (ext[:, 2] > 1.6) & (np.arange(len(ext)) != main))] = 'door'
    roof_i = (bmin[:, 2] > 6.2)
    chim = roof_i & (es[:, 1] < 0.8) & (bmax[:, 2] > 8.2)
    cls[P(fid, roof_i & ~chim)] = 'roof'
    cls[P(fid, chim)] = 'wall'
    plants(c, fid, bmin, bmax, cls)
    cls[fid == main] = 'wall'
    # plinth: big island hugging the ground
    pl = (bmin[:, 2] < 0.05) & (bmax[:, 2] < 1.2) & (ia > 8)
    cls[P(fid, pl)] = 'plinth'
    return o, cls

def house_recipes():
    def wall():
        m = M('wall')
        clean = m.tint(m.tex('cafe_plaster', 2.2, blend=0.2), (1.0, 0.96, 0.88))
        worn = m.tex('house_plaster', (3.0, 3.0, 6.6), blend=0.2)
        f = m.ramp(m.noise(0.45, 3), 0.56, 0.64)
        return m.out(m.mix(f, clean, worn), bump=0.25)
    def plinth():
        m = M('plinth'); return m.out(m.tex('house_steps', 1.0), bump=0.3)
    def roof():
        m = M('roof'); return m.out(m.tex('house_roof', 1.8, blend=0.3), bump=0.5)
    def wood():
        m = M('wood'); return m.out(m.tex('house_shutters', 0.9), bump=0.3)
    def door():
        m = M('door'); return m.out(m.tex('house_door', 1.0), bump=0.3)
    def iron():
        m = M('iron'); return m.out(m.tex('house_iron', 0.4), rough=0.5, metal=0.6, bump=0.1)
    def step():
        m = M('step'); return m.out(m.tex('house_steps', 0.8), bump=0.3)
    def pot():
        m = M('pot'); return m.out(m.tint(m.tex('house_roof', 0.3), (1.0, 0.9, 0.85)), bump=0.1)
    def leaf():
        m = M('leaf'); return m.out(m.hue(m.tex('boulder_moss', 0.3), 0.5, 1.1, 0.9), bump=0.1)
    return dict(wall=wall, plinth=plinth, roof=roof, wood=wood, door=door, iron=iron, step=step, pot=pot, leaf=leaf)


def barn():
    o = load('old_countryside_farm_barn', scale=12)
    c, n, ar, fid, bmin, bmax, main, ia = ctx(o)
    ext = bmax - bmin; P = per_island; N = len(ext)
    cls = np.array(['trim'] * len(c), dtype=object)
    order = np.argsort(-ia)
    roof = [i for i in order[:6] if bmax[i, 2] > 8.0 and bmin[i, 2] > 3.0]
    cls[P(fid, np.isin(np.arange(N), roof))] = 'roof'
    cls[P(fid, (bmin[:, 2] > 8.0))] = 'roof'
    wall = [i for i in order[:6] if bmin[i, 2] < 0.3 and bmax[i, 2] > 7.0]
    w = P(fid, np.isin(np.arange(N), wall))
    cls[w] = 'wood'; cls[w & (c[:, 2] < 1.5)] = 'stone'
    base = [i for i in order[:8] if bmin[i, 2] < 0.2 and bmax[i, 2] < 2.0 and ia[i] > 30]
    cls[P(fid, np.isin(np.arange(N), base))] = 'stone'
    hay = (bmin[:, 2] < 0.2) & (ext[:, 2] > 0.6) & (ext[:, 2] < 1.4) & (ext.max(1) > 1.0) & (ext.max(1) < 2.6) & ~np.isin(np.arange(N), base)
    cls[P(fid, hay)] = 'hay'
    tuft = (ext.max(1) < 0.6) & (bmax[:, 2] < 1.3)
    cls[P(fid, tuft)] = 'grass'
    return o, cls

def barn_recipes():
    def roof():
        m = M('roof'); return m.out(m.tex('barn_roof', 4.2, blend=0.2), rough=0.6, bump=0.5)
    def wood():
        m = M('wood'); return m.out(m.tex('barn_wood', (2.0, 2.0, 2.4), offs=(0, 0, -0.62), blend=0.15), bump=0.4)
    def trim():
        m = M('trim'); return m.out(m.tint(m.tex('barn_wood', 1.2), (0.75, 0.68, 0.6)), bump=0.3)
    def stone():
        m = M('stone'); return m.out(m.tex('barn_stone', 1.8, blend=0.3), bump=0.6)
    def hay():
        m = M('hay'); return m.out(m.tex('barn_hay', 0.9, blend=0.4), bump=0.5)
    def grass():
        m = M('grass'); return m.out(m.tex('cliff_top', 0.6), bump=0.2)
    return dict(roof=roof, wood=wood, trim=trim, stone=stone, hay=hay, grass=grass)


def lighthouse():
    o = load('coastal_lighthouse', height=20)
    c, n, ar, fid, bmin, bmax, main, ia = ctx(o)
    ext = bmax - bmin; es = np.sort(ext, 1); P = per_island; N = len(ext); idx = np.arange(N)
    xc = (bmin[:, 0] + bmax[:, 0]) / 2
    cls = np.array(['iron'] * len(c), dtype=object)
    m = fid == main
    cls[m] = 'tower'
    top = (bmin[:, 2] > 12.8)
    corbel = top & (bmin[:, 2] < 13.6) & (ia > 20)
    cls[P(fid, corbel)] = 'red'
    lbase = top & (bmin[:, 2] > 14.0) & (bmin[:, 2] < 14.5) & (ext[:, 2] > 0.8) & (ia > 10)
    cls[P(fid, lbase)] = 'tower'
    lant = top & (bmin[:, 2] > 15.2) & (bmax[:, 2] < 17.5) & (es[:, 1] > 0.25)
    cls[P(fid, lant) & (ar > 0.01)] = 'glass'
    cot = (bmax[:, 2] < 4.3) & (xc > 0.9)
    cotwall = cot & (ia > 20)
    cls[P(fid, cot)] = 'frame'
    cls[P(fid, cotwall)] = 'cottage'
    cls[P(fid, cot & (bmin[:, 2] > 2.2) & (ext[:, 2] > 0.6))] = 'croof'
    cls[P(fid, cot) & (c[:, 2] > 2.3) & (n[:, 2] > 0.35)] = 'croof'
    cls[P(fid, cot & (bmax[:, 2] < 0.6) & (ia > 1))] = 'cottage'
    return o, cls

def lighthouse_recipes():
    def tower():
        m = M('tower'); z = m.pz()
        band = m.math('MULTIPLY', m.ramp(z, 7.15, 7.25), m.ramp(z, 9.65, 9.55))
        return m.out(m.mix(band, m.tex('light_tower', 2.0, blend=0.3), m.tex('light_red_b', 2.0, blend=0.3)), bump=0.3)
    def red():
        m = M('red'); return m.out(m.tex('light_red_b', 2.0, blend=0.3), bump=0.3)
    def iron():
        m = M('iron'); return m.out(m.tex('light_iron_b', 0.8), rough=0.5, metal=0.5, bump=0.2)
    def glass():
        m = M('glass'); return m.out(m.rgb((0.55, 0.6, 0.55)), rough=0.05, bump=0)
    def frame():
        m = M('frame'); return m.out(m.tex('light_frame_b', 0.7), bump=0.1)
    def cottage():
        m = M('cottage'); return m.out(m.tex('light_cottage_b', (2.5, 2.5, 3.5), offs=(0, 0, -0.12), blend=0.2), bump=0.25)
    def croof():
        m = M('croof'); return m.out(m.tex('light_roof', 1.4, blend=0.3), bump=0.5)
    return dict(tower=tower, red=red, iron=iron, glass=glass, frame=frame, cottage=cottage, croof=croof)


def petrol():
    o = load('modern_petrol_station', scale=12)
    c, n, ar, fid, bmin, bmax, main, ia = ctx(o)
    ext = bmax - bmin; P = per_island
    cls = np.array(['iron'] * len(c), dtype=object)
    cls[P(fid, (ext[:, 2] > 0.6) & (ext[:, 2] < 1.6) & (ia > 0.8))] = 'alu'
    cls[P(fid, (ext[:, 2] > 1.4) & (ia > 2))] = 'pump'
    cls[P(fid, (bmin[:, 2] > 2.3) & (bmax[:, 2] < 3.1) & (ia > 1))] = 'pumptop'
    cls[P(fid, ext[:, 2] > 3.5)] = 'alu'
    cls[P(fid, (bmax[:, 2] < 0.5) & (ia > 4))] = 'kerb'
    can = P(fid, bmin[:, 2] > 4.6)
    cls[can] = 'canopy'
    cls[can & (np.abs(n[:, 2]) < 0.5)] = 'fascia'
    return o, cls

def petrol_recipes():
    def canopy():
        m = M('canopy'); return m.out(m.tex('petrol_canopy', 2.0, blend=0.2), rough=0.4, bump=0.15)
    def fascia():
        m = M('fascia'); return m.out(m.tint(m.tex('petrol_canopy', 1.5, blend=0.2), (0.12, 0.45, 0.32)), rough=0.35, bump=0.1)
    def pump():
        m = M('pump'); return m.out(m.tex('petrol_pump', 0.8), rough=0.35, bump=0.1)
    def pumptop():
        m = M('pumptop'); return m.out(m.tint(m.tex('petrol_pump', 0.8), (0.12, 0.45, 0.32)), rough=0.35, bump=0.1)
    def alu():
        m = M('alu'); return m.out(m.tex('petrol_alu', 0.8), rough=0.4, metal=0.3, bump=0.05)
    def kerb():
        m = M('kerb'); return m.out(m.tex('petrol_kerb', 1.0), bump=0.3)
    def iron():
        m = M('iron'); return m.out(m.tex('house_iron', 0.4), rough=0.5, bump=0.1)
    return dict(canopy=canopy, fascia=fascia, pump=pump, pumptop=pumptop, alu=alu, kerb=kerb, iron=iron)


def bridge():
    o = load('old_stone_arch_bridge', scale=22)
    c, n, ar, fid, bmin, bmax, main, ia = ctx(o)
    ext = bmax - bmin; P = per_island
    cls = np.array(['stone'] * len(c), dtype=object)
    para = (bmin[:, 2] > 2.8) & (ext[:, 1] > 3)
    pf = P(fid, para)
    cls[pf & (n[:, 2] > 0.6)] = 'cap'
    deck = (c[:, 2] > 3.2) & (c[:, 2] < 3.9) & (n[:, 2] > 0.85) & (np.abs(c[:, 0]) < 1.55) & ~pf
    cls[deck] = 'road'
    return o, cls

def bridge_recipes():
    def stone():
        m = M('stone'); return m.out(m.tex('bridge_stone', 2.2, blend=0.25), bump=0.5)
    def cap():
        m = M('cap'); return m.out(m.hue(m.tex('bridge_cap', 1.2, proj='FLAT'), 0.5, 0.7, 1.0), bump=0.3)
    def road():
        m = M('road'); return m.out(m.tex('bridge_road', 2.5, proj='FLAT'), bump=0.4)
    return dict(stone=stone, cap=cap, road=road)


def pine():
    o = load('mediterranean_stone_pine', height=11)
    c, n, ar, fid, bmin, bmax, main, ia = ctx(o)
    cls = np.array(['needle'] * len(c), dtype=object)
    cls[fid == main] = 'bark'
    ext = bmax - bmin
    cls[per_island(fid, (np.sort(ext, 1)[:, 1] < 0.35) & (ext.max(1) > 0.8))] = 'bark'
    return o, cls

def pine_recipes():
    def bark():
        m = M('bark'); return m.out(m.tex('pine_bark', (0.8, 0.8, 1.6), blend=0.4), bump=0.6)
    def needle():
        m = M('needle')
        t = m.tex('pine_needles', 0.9, blend=0.5)
        g = m.n.new('ShaderNodeRGBToBW'); m.l.new(t, g.inputs[0])
        mask = m.ramp(g.outputs[0], 0.04, 0.16)
        base = m.rgb((0.10, 0.20, 0.08))
        col = m.mix(mask, base, m.hue(t, 0.5, 1.05, 1.1))
        col = m.mix(m.ramp(m.noise(0.6), 0.35, 0.65), col, m.tint(col, (0.85, 0.95, 0.7)))
        return m.out(col, rough=0.8, bump=0.4)
    return dict(bark=bark, needle=needle)


def tree_generic(fn, height):
    global IN_OVERRIDE
    import tlib; tlib.IN = '/home/claude/tripo/in2/'
    o = load(fn, height=height)
    c, n, ar, fid, bmin, bmax, main, ia = ctx(o)
    ext = bmax - bmin; es = np.sort(ext, 1); H = height
    r = np.hypot(c[:, 0], c[:, 1])
    cls = np.array(['leaf'] * len(c), dtype=object)
    thin = (es[:, 1] < 0.03 * H) & (es[:, 2] > 0.2 * H)           # long thin branch islands
    cls[per_island(fid, thin)] = 'bark'
    tz = 0.1 if fn == 'tree_cypress' else 0.3
    trunk = (c[:, 2] < tz * H) | ((r < 0.07 * H) & (c[:, 2] < 0.55 * H) & (fn != 'tree_cypress'))
    cls[((fid == main) | (bmax[fid, 2] < 0.35 * H)) & trunk] = 'bark'
    if fn == 'tree_pine2': cls[c[:, 2] < 0.45 * H] = 'bark'
    return o, cls

def tree_recipes(bark_img, leaf_img, base, tint=(1, 1, 1), bark_tile=(0.8, 0.8, 1.6)):
    def bark():
        m = M('bark'); return m.out(m.tex(bark_img, bark_tile, blend=0.4), bump=0.6)
    def leaf():
        m = M('leaf'); t = m.tex(leaf_img, 0.7, blend=0.5)
        g = m.n.new('ShaderNodeRGBToBW'); m.l.new(t, g.inputs[0])
        col = m.mix(m.ramp(g.outputs[0], 0.04, 0.16), m.rgb(base), m.tint(t, tint))
        col = m.mix(m.ramp(m.noise(0.5), 0.35, 0.65), col, m.tint(col, (0.82, 0.92, 0.72)))
        return m.out(col, rough=0.8, bump=0.35)
    return lambda: dict(bark=bark, leaf=leaf)

TREES = {
  'pine2':   ('tree_pine2', 12, 'pine_bark', 'pine_needles', (0.09, 0.17, 0.07), (1.0, 1.05, 0.95), (0.8, 0.8, 1.6)),
  'oak':     ('tree_oak', 10, 'oak_bark', 'oak_leaf', (0.08, 0.16, 0.06), (1.0, 1.0, 1.0), (0.9, 0.9, 1.5)),
  'olive':   ('tree_olive', 5.5, 'oak_bark', 'olive_leaf', (0.16, 0.2, 0.15), (1.05, 1.08, 1.05), (0.7, 0.7, 1.0)),
  'cypress': ('tree_cypress', 14, 'pine_bark', 'olive_leaf', (0.04, 0.1, 0.04), (0.55, 0.75, 0.5), (0.6, 0.6, 1.2)),
}
B = {'cafe': (cafe, cafe_recipes, 'bld_cafe'), 'house': (house, house_recipes, 'bld_house'), 'barn': (barn, barn_recipes, 'bld_barn'), 'lighthouse': (lighthouse, lighthouse_recipes, 'bld_lighthouse'), 'petrol': (petrol, petrol_recipes, 'bld_petrol'), 'bridge': (bridge, bridge_recipes, 'bld_bridge'), 'pine': (pine, pine_recipes, 'tree_pine')}
if which in TREES:
    t = TREES[which]; B[which] = (lambda t=t: tree_generic(t[0], t[1]), tree_recipes(*t[2:]), 'tree_' + which)
    LO['tree_' + which] = 6500; TREE_KW.update(ao_strength=0.4, ao_dist=0.8)
fn, rec, name = B[which]
o, cls = fn()
print('CLASSES', {k: int((cls == k).sum()) for k in set(cls)})
if debug:
    debug_render(o, list(cls), which)
else:
    kw = dict(ao_dist=1.2, ao_samples=16); kw.update(TREE_KW)
    build(o, list(cls), rec(), name, res=2048, **kw)
