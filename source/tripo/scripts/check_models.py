import bpy, bmesh, sys, glob, os, json
from mathutils import Vector
out={}
for f in sorted(glob.glob('/home/claude/tripo/in/*.fbx')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    r={'objs':[]}
    for o in bpy.data.objects:
        d={'name':o.name,'type':o.type,'loc':[round(x,3) for x in o.location],'rot':[round(x,3) for x in o.rotation_euler],'scale':[round(x,4) for x in o.scale],'parent':o.parent.name if o.parent else None}
        if o.type=='MESH':
            me=o.data
            bm=bmesh.new(); bm.from_mesh(me); bm.transform(o.matrix_world)
            vs=[v.co for v in bm.verts]
            mn=Vector((min(v.x for v in vs),min(v.y for v in vs),min(v.z for v in vs)));mx=Vector((max(v.x for v in vs),max(v.y for v in vs),max(v.z for v in vs)))
            d['verts']=len(bm.verts);d['tris']=sum(len(f.verts)-2 for f in bm.faces);d['faces']=len(bm.faces)
            d['size']=[round(x,3) for x in (mx-mn)];d['min']=[round(x,3) for x in mn]
            d['nonmanifold_e']=sum(1 for e in bm.edges if not e.is_manifold)
            d['boundary_e']=sum(1 for e in bm.edges if e.is_boundary)
            d['loose_v']=sum(1 for v in bm.verts if not v.link_edges)
            d['zero_area']=sum(1 for f in bm.faces if f.calc_area()<1e-10)
            # duplicates
            import collections
            c=collections.Counter((round(v.co.x,5),round(v.co.y,5),round(v.co.z,5)) for v in bm.verts)
            d['dup_v']=sum(n-1 for n in c.values() if n>1)
            # islands
            bm.verts.ensure_lookup_table()
            seen=set();isl=0
            for v in bm.verts:
                if v.index in seen: continue
                isl+=1;st=[v]
                while st:
                    x=st.pop()
                    if x.index in seen: continue
                    seen.add(x.index)
                    for e in x.link_edges: st.append(e.other_vert(x))
            d['islands']=isl
            # normals outward test: signed volume
            vol=0
            for fc in bm.faces:
                p=[l.vert.co for l in fc.loops]
                for i in range(1,len(p)-1): vol+=p[0].dot(p[i].cross(p[i+1]))/6
            d['signed_vol']=round(vol,3)
            d['uv_layers']=[u.name for u in me.uv_layers]
            d['mats']=[]
            for m in me.materials:
                md={'name':m.name if m else None}
                if m and m.use_nodes:
                    md['imgs']=[(n.image.name,n.image.size[:]) for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
                d['mats'].append(md)
            d['vcol']=[a.name for a in me.color_attributes]
            bm.free()
        r['objs'].append(d)
    r['images']=[(i.name,i.size[:],i.filepath) for i in bpy.data.images]
    out[os.path.basename(f)]=r
json.dump(out,open('/home/claude/tripo/inspect.json','w'),indent=1)
