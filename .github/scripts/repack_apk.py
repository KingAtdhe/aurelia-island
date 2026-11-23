"""Re-zip a Godot APK with deflate on the imported .ctex textures.
Godot's Android exporter always stores .ctex uncompressed (it assumes they are already compressed), but ETC2 data
deflates to roughly half. Android reads deflated assets transparently through AAssetManager, which is all
FileAccessAndroid uses. The old v1 signature files are dropped; zipalign + apksigner run afterwards.
usage: python3 repack_apk.py in.apk out.apk"""
import sys, zipfile, zlib
src, out = sys.argv[1:3]
zi = zipfile.ZipFile(src); zo = zipfile.ZipFile(out, 'w')
before = after = 0
for i in zi.infolist():
    n = i.filename
    if n.startswith('META-INF/') and n.rsplit('.', 1)[-1] in ('SF', 'RSA', 'EC', 'DSA', 'MF'): continue
    d = zi.read(n); ct = i.compress_type
    if n.endswith('.ctex') and ct == zipfile.ZIP_STORED and len(zlib.compress(d, 6)) < 0.9 * len(d): ct = zipfile.ZIP_DEFLATED
    ni = zipfile.ZipInfo(n, date_time=i.date_time); ni.compress_type = ct; ni.external_attr = i.external_attr
    zo.writestr(ni, d, compress_type=ct, compresslevel=9 if ct == zipfile.ZIP_DEFLATED else None)
zo.close()
import os; print('repacked %.1f MB -> %.1f MB' % (os.path.getsize(src) / 1048576, os.path.getsize(out) / 1048576))
