import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from tlib import *

which = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['boulder', 'slab', 'stones', 'cliff', 'corner']

def small_islands(o, lim):
    fid, boxes = islands(o)
    big = [max(b[1] - b[0]) for b in boxes]
    return np.array([big[i] < lim for i in fid]), np.array(fid), boxes

if 'boulder' in which:
    o = load('large_weathered_granite_boulder', height=1.4)
    m = M('boulder')
    rock = m.tex('boulder_rock', 0.9)
    moss = m.tex('boulder_moss', 0.6)
    f = m.math('MULTIPLY', m.ramp(m.nz(), 0.5, 0.85), m.ramp(m.noise(1.2), 0.42, 0.58))
    m.out(m.mix(f, rock, moss))
    assign(o, [m], [0] * len(o.data.polygons))
    bake(o, 'rock_boulder', res=1024, lo_tris=1000)

if 'slab' in which:
    o = load('low_flat_granite_rock_slab', scale=3.0)
    m = M('slab')
    top = m.tex('slab_top', 1.0, proj='FLAT')
    edge = m.tex('slab_edge', 0.5)
    m.out(m.mix(m.ramp(m.nz(), 0.45, 0.7), edge, top))
    assign(o, [m], [0] * len(o.data.polygons))
    bake(o, 'rock_slab', res=1024, lo_tris=1300)

if 'stones' in which:
    o = load('cluster_of_stones', scale=1.3)
    fid, boxes = islands(o)
    rng = np.random.default_rng(3); pick = rng.random(len(boxes)) < 0.45
    face_attr(o, 'isl', [float(pick[i]) for i in fid])
    m = M('stones')
    g = m.tex('stones_granite', 0.35); p = m.tex('stones_pebble', 0.35)
    m.out(m.mix(m.attr('isl'), g, p), bump=0.25)
    assign(o, [m], [0] * len(o.data.polygons))
    bake(o, 'rock_stones', res=1024, ao_dist=0.25, lo_tris=1100)

if 'cliff' in which:
    o = load('granite_cliff_face', height=8.0)
    sm, fid, boxes = small_islands(o, 0.6)
    face_attr(o, 'isl', sm.astype(float))
    m = M('cliff')
    rock = m.tex('cliff_rock', 3.0)
    top = m.tex('cliff_top', 2.0)
    f = m.math('MAXIMUM', m.ramp(m.nz(), 0.55, 0.8), m.attr('isl'))
    m.out(m.mix(f, rock, top))
    assign(o, [m], [0] * len(o.data.polygons))
    bake(o, 'rock_cliff', res=2048, ao_dist=1.5, lo_tris=2400)

if 'corner' in which:
    o = load('granite_rock_cliff', height=8.0)
    sm, fid, boxes = small_islands(o, 0.6)
    face_attr(o, 'isl', sm.astype(float))
    m = M('corner')
    rock = m.tex('corner_rock', 3.0)
    scree = m.tex('corner_scree', 2.0)
    top = m.tex('cliff_top', 2.0)
    up = m.ramp(m.nz(), 0.6, 0.85)
    low = m.ramp(m.pz(), 1.8, 1.0)
    c = m.mix(up, rock, m.mix(low, top, scree))
    c = m.mix(m.attr('isl'), c, scree)
    m.out(c)
    assign(o, [m], [0] * len(o.data.polygons))
    bake(o, 'rock_corner', res=2048, ao_dist=1.5, lo_tris=1600)
