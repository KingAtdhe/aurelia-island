"""Packs the exported GLBs for the hosted game: dedup + quantize (+ meshopt), then raw binary parts of at most 12 MiB with a small JSON manifest (PACK_B64=1 for the old base64 JSON parts)."""
import subprocess, base64, json, os, sys, shutil, glob
import os as _os
SRC = '/home/claude/isle/out'; SITE = _os.environ.get('SITE', 'site'); FULL = _os.environ.get('FULL') == '1'
def run(*a): subprocess.run(['npx', '--no-install', 'gltf-transform', *a], check=True, stdout=subprocess.DEVNULL)
def pack(path, base):
    for f in [base + '.json'] + glob.glob(base + '.p*.json'):
        if os.path.exists(f): os.remove(f)
    for f in glob.glob(base + '.p*.wasm') + glob.glob(base + '.p*.bin'): os.remove(f)
    b = open(path, 'rb').read()
    if os.environ.get('PACK_B64') != '1':                                  # raw binary parts (default): a third smaller than base64
        CH = (40 if FULL else 12) * 1024 * 1024; parts = [b[i:i + CH] for i in range(0, len(b), CH)]
        json.dump(dict(bytes=len(b), parts=len(parts), fmt='bin', ext='bin' if FULL else 'wasm', sizes=[len(q) for q in parts]), open(base + '.json', 'w'))
        for k, q in enumerate(parts): open('%s.p%d.%s' % (base, k, 'bin' if FULL else 'wasm'), 'wb').write(q)
        print(base, round(len(b) / 1e6, 1), 'MB binary'); return
    s = base64.b64encode(b).decode(); CH = 9 * 1024 * 1024 // 3 * 4
    if len(s) <= CH: json.dump(dict(bytes=len(b), b64=s), open(base + '.json', 'w'))
    else:
        parts = [s[i:i + CH] for i in range(0, len(s), CH)]; json.dump(dict(bytes=len(b), parts=len(parts)), open(base + '.json', 'w'))
        for k, p in enumerate(parts): json.dump(dict(b64=p), open('%s.p%d.json' % (base, k), 'w'))
    print(base, round(len(b) / 1e6, 1), 'MB')
def jpegify(src, dst, q=80, top=2048):
    if FULL: q, top = 90, 1 << 16
    """Re-encode the opaque PNG textures inside a GLB as JPEG (much smaller); textures with alpha stay PNG."""
    import struct, io
    from PIL import Image
    d = open(src, 'rb').read(); jl = struct.unpack('<I', d[12:16])[0]; J = json.loads(d[20:20 + jl]); B = d[20 + jl + 8:]
    new = {}
    for im in J.get('images', []):
        bv = J['bufferViews'][im['bufferView']]; raw = B[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]; pic = Image.open(io.BytesIO(raw))
        if pic.mode in ('RGBA', 'LA', 'P') and pic.convert('RGBA').getextrema()[3][0] < 255: continue
        nm_ = im.get('name', '')                                               # ground and road colour up to 2048 px, other colour and normal maps 1024, packed roughness/metal 512
        cap = top if (FULL or (nm_.startswith('tex_photo_') and not nm_.endswith(('_n', '_orm')))) else (512 if nm_.endswith('_orm') else min(1024, top))
        if pic.width > cap: pic = pic.resize((cap, int(cap * pic.height / pic.width)), Image.LANCZOS)
        o = io.BytesIO(); pic.convert('RGB').save(o, 'JPEG', quality=q, subsampling=0); new[im['bufferView']] = o.getvalue(); im['mimeType'] = 'image/jpeg'
    out = bytearray()
    for i, bv in enumerate(J['bufferViews']):
        blob = new.get(i, B[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])
        while len(out) % 4: out.append(0)
        bv['byteOffset'] = len(out); bv['byteLength'] = len(blob); out += blob
    while len(out) % 4: out.append(0)
    J['buffers'][0]['byteLength'] = len(out); js = json.dumps(J, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
    open(dst, 'wb').write(b'glTF' + struct.pack('<II', 2, 28 + len(js) + len(out)) + struct.pack('<I', len(js)) + b'JSON' + js + struct.pack('<I', len(out)) + b'BIN\0' + bytes(out))
Q = ['--quantize-position', '16', '--quantize-normal', '8', '--quantize-texcoord', '14', '--quantize-color', '8']
def node(*a): subprocess.run(['node', *a], check=True)
node('split.mjs', f'{SRC}/aurelia_game.glb', '/tmp/s_core.glb', '/tmp/s_det.glb'); node('split.mjs', f'{SRC}/aurelia_game_lite.glb', '/tmp/s_corel.glb', '/tmp/s_detl.glb')
node('split.mjs', f'{SRC}/aurelia_flora.glb', '/tmp/f_pl.glb', '/tmp/f_kit.glb', '^FLORA_prop_')
for src, name, lite in (('/tmp/s_core.glb', 'island', '/tmp/s_corel.glb'), ('/tmp/s_det.glb', 'islandd', '/tmp/s_detl.glb'), ('/tmp/f_pl.glb', 'flora', '/tmp/f_pl.glb'), ('/tmp/f_kit.glb', 'florak', '/tmp/f_kit.glb')):
    node('flatten.mjs', src, '/tmp/a0.glb')
    if name == 'island' and not FULL:                                        # High quality loads a copy of the start file with 2048 px ground and road textures
        jpegify('/tmp/a0.glb', '/tmp/a1h.glb', top=2048); run('meshopt', '/tmp/a1h.glb', '/tmp/islandh_c.glb'); pack('/tmp/islandh_c.glb', f'{SITE}/map/islandhc')
    jpegify('/tmp/a0.glb', '/tmp/a1.glb', top=1024); run('meshopt', '/tmp/a1.glb', f'/tmp/{name}_c.glb')
    if not FULL: node('flatten.mjs', lite, '/tmp/b0.glb'); jpegify('/tmp/b0.glb', '/tmp/b1.glb', top=1024); run('quantize', '/tmp/b1.glb', f'/tmp/{name}_q.glb', *Q)
    pack(f'/tmp/{name}_c.glb', f'{SITE}/map/{name}c')
    if not FULL: pack(f'/tmp/{name}_q.glb', f'{SITE}/map/{name}')
shutil.copy(f'{SRC}/world.json', f'{SITE}/data/world.json'); shutil.copy(f'{SRC}/flora.json', f'{SITE}/data/flora.json')
b = open(f'{SRC}/height.bin', 'rb').read(); json.dump(dict(bytes=len(b), b64=base64.b64encode(b).decode()), open(f'{SITE}/data/height.json', 'w'))
json.dump(dict(png=base64.b64encode(open(f'{SRC}/ground_shade.png', 'rb').read()).decode()), open(f'{SITE}/data/shade.json', 'w'))
if not FULL: shutil.copy('/tmp/island_c.glb', f'{SRC}/aurelia_island_compressed.glb'); shutil.copy('/tmp/islandd_c.glb', f'{SRC}/aurelia_island_detail_compressed.glb')
