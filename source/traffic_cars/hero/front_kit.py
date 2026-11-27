"""Front-end detail shared by the traffic parts scripts: grille blocks sitting in the grille recess, projector headlamps
(clear lens dome over a chrome reflector bowl). Called with the parts script's own helpers (surf point, B, obj, blob)."""
import numpy as np, bmesh
from mathutils import Vector, Matrix

def grille_blocks(sp, B, obj, y0, y1, z0, z1, dy=0.066, dz=0.040, size=(0.012, 0.046, 0.022), inset=0.007, mat='Mesh', taper=0.0):
    bm = bmesh.new()
    for zz in np.arange(z0 + dz / 2, z1 - dz / 4, dz):
        w = y1 - taper * (z1 - zz) / max(z1 - z0, 1e-6)
        for yy in np.arange(-w + dy / 2, w - dy / 4, dy):
            p = sp('yz', yy, zz, 1)
            if p is None: continue
            bmesh.ops.translate(bm, vec=B(p) + Vector((-inset, 0, 0)), verts=bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((*size, 1)))['verts'])
    return obj('GrilleBlocks', bm, mat)

def projector(blob, at, r=0.034, out=0.004):
    """at: a Blender point on the lamp face (front, +X)."""
    blob('Proj_Bowl', at + Vector((-0.006 + out, 0, 0)), (0.016, 2 * r * 1.25, 2 * r * 1.25), 'Chrome', 18, 8)
    blob('Proj_Lens', at + Vector((0.004 + out, 0, 0)), (0.022, 2 * r, 2 * r), 'LampLens', 18, 8)
