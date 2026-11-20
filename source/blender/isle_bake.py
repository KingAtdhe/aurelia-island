"""Light bake for Aurelia Island: indirect light (sky occlusion plus light bounced off the ground and walls) is path-traced by Cycles
per vertex and multiplied into the vertex colours, so it ships inside the model. Results are cached per object in bake_cache.npz."""
import bpy, os, time
import numpy as np
import isle_lib as L
SETS = ('TunnelPortal', 'Houses', 'Roofs', 'KitTrim', 'ArchTrim', 'Structures', 'Pavement', 'Road', 'Verge', 'Bridges')


def wanted(o):
    b = o.name.split('__')[0]
    return o.type == 'MESH' and (b in SETS or b.startswith('BuildingsHD') or (b.startswith('Terrain') and not b.startswith('TerrainBlend'))) and not o.name.startswith('KIT_')


def bake(out, samples=20):
    scn = bpy.context.scene; path = os.path.join(out, 'bake_cache.npz'); cache = dict(np.load(path)) if os.path.exists(path) else {}
    hidden = []
    for o in bpy.data.objects:
        b = o.name.split('__')[0]
        if (b in ('TreeCards', 'GrassCards') or b.startswith('BuildingsLOD') or b.startswith('KIT_') or b.startswith('TerrainBlend') or b == 'ContactAO') and not o.hide_render: o.hide_render = True; hidden.append(o)
    scn.cycles.samples = samples; scn.cycles.max_bounces = 3; scn.render.bake.target = 'VERTEX_COLORS'; bk = scn.render.bake
    bk.use_pass_direct = False; bk.use_pass_indirect = True; bk.use_pass_color = False
    objs = [o for o in bpy.data.objects if wanted(o)]; t0 = time.time(); nb = 0; res = {}
    for o in objs:
        me = o.data; nl = len(me.loops); key = o.name
        if key in cache and len(cache[key]) == nl * 3: res[key] = cache[key].reshape(-1, 3); continue
        a = me.color_attributes.new('BakeLight', 'FLOAT_COLOR', 'CORNER'); me.color_attributes.active_color = a
        for q in bpy.context.selected_objects: q.select_set(False)
        o.select_set(True); bpy.context.view_layer.objects.active = o
        try:
            bpy.ops.object.bake(type='DIFFUSE'); v = np.empty(nl * 4, np.float32); me.color_attributes['BakeLight'].data.foreach_get('color', v); res[key] = v.reshape(-1, 4)[:, :3].copy(); nb += 1
        except Exception as e: print('bake failed', o.name, e)
        me.color_attributes.remove(me.color_attributes['BakeLight']); me.color_attributes.active_color = me.color_attributes['Col']; o.select_set(False)
    if not res: return
    def vavg(me, m):                                                              # one value per vertex, so vertices stay shared in the exported files
        li = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', li); m = np.asarray(m, float).reshape(len(li), -1); nv = len(me.vertices); cnt = np.maximum(np.bincount(li, minlength=nv), 1)
        return np.stack([np.bincount(li, weights=m[:, k], minlength=nv) / cnt for k in range(m.shape[1])], 1)[li]
    def nz(o):
        me = o.data; n = np.empty(len(me.loops) * 3, np.float32)
        try: me.corner_normals.foreach_get('vector', n)
        except Exception: me.loops.foreach_get('normal', n)
        return n.reshape(-1, 3)[:, 2]
    up_l = np.concatenate([res[o.name].mean(1)[nz(o) > 0.9] for o in objs if o.name in res and o.name.startswith('Terrain')]); ref = float(np.percentile(up_l, 80)) + 1e-6
    tp = []; tf = []; fs = []; terr = []
    for o in objs:
        if o.name not in res: continue
        r = res[o.name]; l = r.mean(1); e = ref * (0.42 + 0.58 * (0.5 + 0.5 * nz(o)))            # what an unshadowed surface facing that way would receive
        f = np.clip(l / e, 0.0, 1.25); f = 0.45 + 0.55 * np.clip(f, 0, 1) ** 0.9 + 0.06 * np.clip(f - 1, 0, 0.25) / 0.25; fs.append(f)
        if o.name.startswith('Terrain'):
            me_ = o.data; li = np.empty(len(me_.loops), np.int32); me_.loops.foreach_get('vertex_index', li); co = np.empty(len(me_.vertices) * 3, np.float32); me_.vertices.foreach_get('co', co); tp.append(co.reshape(-1, 3)[li, :2]); tf.append(f); terr.append(o); continue
        tint = r / np.maximum(l[:, None], 1e-6); tint = 0.72 + 0.28 * np.clip(tint, 0.6, 1.5)
        me = o.data; ca = me.color_attributes['Col']; c = np.empty(len(me.loops) * 4, np.float32); ca.data.foreach_get('color', c); c = c.reshape(-1, 4)
        mlt = vavg(me, f[:, None] * tint); c[:, :3] = np.clip(c[:, :3] * mlt, 0, 1); ca.data.foreach_set('color', c.ravel()); me.color_attributes.active_color = ca
        try: me.color_attributes.render_color_index = list(me.color_attributes).index(ca)
        except Exception: pass
    from scipy.spatial import cKDTree
    tr = cKDTree(np.vstack(tp)); tfa = np.concatenate(tf)
    TP = np.vstack(tp); sm = np.empty(len(tfa), np.float32)                                # the ground keeps only broad shading (under trees, beside buildings): average over about 15 m
    for i0 in range(0, len(TP), 100000): sm[i0:i0 + 100000] = tfa[tr.query(TP[i0:i0 + 100000], k=24, distance_upper_bound=16.0)[1].clip(0, len(tfa) - 1)].mean(1)
    tfa = sm; k0 = 0
    for o in terr:
        me = o.data; n_ = len(me.loops); f = tfa[k0:k0 + n_]; k0 += n_; ca = me.color_attributes['Col']; c = np.empty(n_ * 4, np.float32); ca.data.foreach_get('color', c); c = c.reshape(-1, 4); c[:, :3] *= vavg(me, f); ca.data.foreach_set('color', c.ravel()); me.color_attributes.active_color = ca                                   # the overlay ground takes the bake of the ground under it
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith('TerrainBlend'):
            me = o.data; li = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', li); co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co)
            f = tfa[tr.query(co.reshape(-1, 3)[li, :2])[1]]; ca = me.color_attributes['Col']; c = np.empty(len(me.loops) * 4, np.float32); ca.data.foreach_get('color', c); c = c.reshape(-1, 4); c[:, :3] *= vavg(me, f); ca.data.foreach_set('color', c.ravel())
    lum = np.concatenate(fs)
    np.savez_compressed(path, **{k: v.astype(np.float16).ravel() for k, v in res.items()})
    for o in hidden: o.hide_render = False
    L.STATS['light_bake'] = dict(objects=len(res), baked_now=nb, seconds=int(time.time() - t0), samples=samples, mean_factor=round(float(lum.mean()), 2))
