// Saba's Tripo props: merge the species GLBs into one file, shrink textures for phones, meshopt.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, textureCompress, meshopt, mergeDocuments, unpartition, simplifyPrimitive } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptSimplifier } from 'meshoptimizer';
import sharp from 'sharp';
import fs from 'fs';
const [dir, dst] = process.argv.slice(2);
await MeshoptEncoder.ready; await MeshoptSimplifier.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder });
const files = fs.readdirSync(dir).filter(f => f.endsWith('.glb')).sort();
const doc = await io.read(dir + '/' + files[0]);
for (const f of files.slice(1)) mergeDocuments(doc, await io.read(dir + '/' + f));
const root = doc.getRoot(), scene = root.listScenes()[0];
for (const s of root.listScenes().slice(1)) { for (const n of s.listChildren()) scene.addChild(n); s.dispose(); }
root.setDefaultScene(scene);
await doc.transform(weld({ tolerance: 0.0001 }));
for (const n of root.listNodes()) { const m = /^T_(.+)_LOD0$/.exec(n.getName()); if (!m || !n.getMesh()) continue;
  const tgt = (n.getExtras() || {}).lod1 || 800, mesh = n.getMesh().clone(), n1 = doc.createNode('T_' + m[1] + '_LOD1').setMesh(mesh).setTranslation(n.getTranslation()).setRotation(n.getRotation()).setScale(n.getScale());
  scene.addChild(n1);
  for (const p of mesh.listPrimitives()) { const tri = p.getIndices().getCount() / 3; simplifyPrimitive(p, { simplifier: MeshoptSimplifier, ratio: Math.min(1, tgt / tri), error: /^rock/.test(m[1]) ? 0.12 : 0.03, lockBorder: false });
    console.log(m[1], tri, '->', p.getIndices().getCount() / 3); } }
// texture sizes: building colour 1024, rock colour 512, all normal maps 512
for (const t of root.listTextures()) t.setName((t.getName() || '') + '');
const big = new Set();
for (const m of root.listMaterials()) { const bld = /prop_|rock/.test(m.getName()); const c = m.getBaseColorTexture(); if (c) c.setName(bld ? 'col_big' : 'col_small'); const n = m.getNormalTexture(); if (n) n.setName('nrm'); }
await doc.transform(dedup(), unpartition(), weld({ tolerance: 0.0001 }),
  textureCompress({ encoder: sharp, targetFormat: 'jpeg', resize: [1024, 1024], pattern: /^col_big/, quality: 84 }),
  textureCompress({ encoder: sharp, targetFormat: 'jpeg', resize: [512, 512], pattern: /^(col_small|nrm)/, quality: 84 }),
  prune({ keepAttributes: false }), meshopt({ encoder: MeshoptEncoder, level: 'medium' }));
await io.write(dst, doc);
console.log('nodes', root.listNodes().map(n => n.getName()).join(' '), 'textures', root.listTextures().map(t => t.getName() + ':' + t.getImage().byteLength).join(' '));
