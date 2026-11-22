import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from tlib import *
fn,s=sys.argv[sys.argv.index('--')+1:][:2]; s=float(s)
views=[(float(a),float(e)) for a,e in [v.split(',') for v in sys.argv[sys.argv.index('--')+3:]]]
o=load(fn,scale=s)
c,n,ar=face_data(o); fid,boxes=islands(o); fid=np.array(fid)
rng=np.random.default_rng(1); cols=rng.random((len(boxes),3))*0.7+0.25
mats=[]
for i in range(len(boxes)):
    m=bpy.data.materials.new(str(i)); m.diffuse_color=tuple(cols[i])+(1,); o.data.materials.append(m)
o.data.polygons.foreach_set('material_index',fid.astype(np.int32))
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.color_type='MATERIAL'; sc.display.shading.light='STUDIO'
sc.render.resolution_x=1400; sc.render.resolution_y=1050
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
co=np.array([v.co[:] for v in o.data.vertices]); mn,mx=co.min(0),co.max(0); ctr=Vector(((mn+mx)/2).tolist()); R=float(np.linalg.norm(mx-mn))/2
cam.data.type='ORTHO'; cam.data.ortho_scale=R*2.1
from PIL import Image, ImageDraw
for k,(az,el) in enumerate(views):
    a=math.radians(az);e=math.radians(el)
    cam.location=ctr+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*R*4
    cam.rotation_euler=(ctr-cam.location).to_track_quat('-Z','Y').to_euler()
    p=f'/tmp/id_{k}.png'; sc.render.filepath=p; bpy.ops.render.render(write_still=True)
    im=Image.open(p).convert('RGB'); d=ImageDraw.Draw(im)
    viewdir=(ctr-cam.location).normalized()
    for i in range(len(boxes)):
        m=fid==i; a_=ar[m].sum()
        if a_<0.15: continue
        # label at the face of the island most facing camera
        idx=np.where(m)[0]; facing=(n[idx]@np.array(viewdir[:]))
        j=idx[np.argmin(facing)]
        if facing.min()>-0.1: continue
        v=world_to_camera_view(sc,cam,Vector(c[j].tolist()))
        x=v.x*im.width; y=(1-v.y)*im.height
        d.text((x-6,y-6),str(i),fill=(0,0,0)); d.text((x-5,y-5),str(i),fill=(255,255,255))
    im.save(f'/home/claude/tripo/ids_{fn[:10]}_{k}.png')
