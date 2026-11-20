// Game version of a sale-pack car: drop lightmap UVs, tangents and the second colour set, resize textures, weld, simplify lightly, meshopt.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, simplify, resample, textureCompress, meshopt } from '@gltf-transform/functions';
import { MeshoptSimplifier, MeshoptEncoder } from 'meshoptimizer';
import sharp from 'sharp';
const [src, dst, ratio = '0.75', tex = '1024'] = process.argv.slice(2);
await MeshoptSimplifier.ready; await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder });
const doc = await io.read(src);
for (const mesh of doc.getRoot().listMeshes()) for (const p of mesh.listPrimitives()) for (const a of ['TEXCOORD_2', 'TANGENT', 'COLOR_1']) { const x = p.getAttribute(a); if (x) p.setAttribute(a, null); }
await doc.transform(dedup(), prune(), weld({ tolerance: 0.0001 }), ...(+ratio < 1 ? [simplify({ simplifier: MeshoptSimplifier, ratio: +ratio, error: 0.0008 })] : []),
  textureCompress({ encoder: sharp, targetFormat: 'jpeg', resize: [+tex, +tex], slots: /^(?!.*(alpha|opacity)).*/, quality: +(process.argv[6] || 82) }), prune(), meshopt({ encoder: MeshoptEncoder, level: 'medium' }));
await io.write(dst, doc);
