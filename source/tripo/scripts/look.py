import bpy, sys, math
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
for name in args:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f'/home/claude/tripo/out/{name}.glb')
    obs=[o for o in bpy.data.objects if o.type=='MESH']
    import numpy as np
    pts=np.array([ (o.matrix_world@v.co)[:] for o in obs for v in o.data.vertices])
    mn,mx=pts.min(0),pts.max(0); c=Vector(((mn+mx)/2).tolist()); R=float(np.linalg.norm(mx-mn))/2
    sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=24; sc.cycles.use_denoising=True
    sc.render.resolution_x=640; sc.render.resolution_y=480
    w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True
    bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(0.55,0.68,0.85,1); bg.inputs[1].default_value=0.9
    sun=bpy.data.objects.new('s',bpy.data.lights.new('s','SUN')); sun.data.energy=3.5; sun.rotation_euler=(math.radians(50),0,math.radians(35)); sun.data.angle=0.05
    sc.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=R*8); g=bpy.context.object
    gm=bpy.data.materials.new('g'); gm.use_nodes=True; gm.node_tree.nodes['Principled BSDF'].inputs[0].default_value=(0.35,0.33,0.28,1); g.data.materials.append(gm)
    sc.view_settings.view_transform='AgX'
    cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=40
    for i,(az,el,d) in enumerate([(30,18,2.6),(210,22,2.6),(120,10,1.25)]):
        a=math.radians(az);e=math.radians(el)
        t=c if i<2 else Vector((c.x,c.y,mn[2]+0.3*(mx[2]-mn[2])))
        cam.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*R*d
        cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=f'/home/claude/tripo/look/{name}_{i}.png'
        bpy.ops.render.render(write_still=True)
