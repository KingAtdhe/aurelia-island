// Drops the normal attribute from meshes that are already flat-shaded (every vertex normal equals its face normal),
// then welds them: three.js shades such meshes flat from screen-space derivatives, so they look the same at a fraction of the vertices.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { weld, dedup } from '@gltf-transform/functions';

const [src, dst] = process.argv.slice(2);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(src);
let flat = 0, kept = 0, vBefore = 0;
for (const mesh of doc.getRoot().listMeshes()) {
  for (const prim of mesh.listPrimitives()) {
    const P = prim.getAttribute('POSITION'), N = prim.getAttribute('NORMAL'), I = prim.getIndices();
    if (!P || !N || !I) { kept++; continue; }
    const p = P.getArray(), n = N.getArray(), idx = I.getArray(); let good = 0, tot = 0;
    for (let t = 0; t < idx.length; t += 3) {
      const a = idx[t] * 3, b = idx[t + 1] * 3, c = idx[t + 2] * 3;
      const ux = p[b] - p[a], uy = p[b + 1] - p[a + 1], uz = p[b + 2] - p[a + 2], vx = p[c] - p[a], vy = p[c + 1] - p[a + 1], vz = p[c + 2] - p[a + 2];
      let fx = uy * vz - uz * vy, fy = uz * vx - ux * vz, fz = ux * vy - uy * vx; const l = Math.hypot(fx, fy, fz); if (l < 1e-12) continue;
      fx /= l; fy /= l; fz /= l; tot++;
      if ([a, b, c].every(k => n[k] * fx + n[k + 1] * fy + n[k + 2] * fz > 0.995)) good++;
    }
    if (tot && good / tot > 0.97) { vBefore += P.getCount(); prim.setAttribute('NORMAL', null); flat++; } else kept++;
  }
}
await doc.transform(dedup(), weld());
let vAfter = 0; for (const mesh of doc.getRoot().listMeshes()) for (const prim of mesh.listPrimitives()) if (!prim.getAttribute('NORMAL')) vAfter += prim.getAttribute('POSITION').getCount();
console.log(`flat primitives ${flat}, smooth kept ${kept}, flat vertices ${vBefore} -> ${vAfter}`);
await io.write(dst, doc);
