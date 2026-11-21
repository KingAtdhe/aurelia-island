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
const DROP = (process.env.DROP || 'TEXCOORD_2,TANGENT,COLOR_1').split(',');
for (const mesh of doc.getRoot().listMeshes()) for (const p of mesh.listPrimitives()) for (const a of DROP) { const x = p.getAttribute(a); if (x) p.setAttribute(a, null); }
if (process.env.PLAIN_PAINT) for (const m of doc.getRoot().listMaterials()) if (m.getName() === process.env.PLAIN_PAINT) m.setBaseColorTexture(null);   // plain paint colour: the game sets it
const PR = () => prune(process.env.KEEPATTR ? { keepAttributes: true } : {});
await doc.transform(dedup(), PR(), weld({ tolerance: 0.0001 }), ...(+ratio < 1 ? [simplify({ simplifier: MeshoptSimplifier, ratio: +ratio, error: 0.0008 })] : []),
  textureCompress({ encoder: sharp, targetFormat: 'jpeg', resize: [+tex, +tex], slots: /^(?!.*(alpha|opacity)).*/, quality: +(process.argv[6] || 82) }), PR(), meshopt({ encoder: MeshoptEncoder, level: 'medium' }));
await io.write(dst, doc);
