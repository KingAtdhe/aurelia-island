"""Write Godot .import settings for a folder of map textures: VRAM compressed (ETC2 on phones), mipmaps, normal maps flagged,
sizes capped so the phone build stays small. usage: python3 tex_imports.py <dir> [color_limit] [normal_limit]"""
import sys, os
D = sys.argv[1]; CL = int(sys.argv[2]) if len(sys.argv) > 2 else 1024; NL = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
T = '''[remap]

importer="texture"
type="CompressedTexture2D"

[params]

compress/mode=2
compress/high_quality=false
compress/lossy_quality=0.7
compress/normal_map=%d
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
roughness/mode=0
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/size_limit=%d
detect_3d/compress_to=1
'''
for f in os.listdir(D):
    if not f.endswith(('.jpg', '.png')): continue
    nm = f.rsplit('.', 1)[0]; normal = nm.endswith('_n') or '_n_' in nm; small = normal or nm.endswith('_orm')
    kit = nm.startswith('tex_kit_') and not any(a in nm for a in ('atlas', 'trim_sheet'))      # building kit materials: tiling, seen at street distance
    open(os.path.join(D, f + '.import'), 'w').write(T % (1 if normal else 2, NL if (small or kit) else CL))
