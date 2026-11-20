// Splits the map into the part needed to start driving and the close-up detail that streams in afterwards.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { prune } from '@gltf-transform/functions';
const [src, coreOut, detOut, rx] = process.argv.slice(2);
const DETAIL = rx ? new RegExp(rx) : /^(BuildingsHD|KitTrim|ArchTrim|Props|RoadDecals|ContactAO|Structures|Shapes|Landmark|TowerCrown|Vegetation)/;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
for (const [out, keepDetail] of [[coreOut, false], [detOut, true]]) {
  const doc = await io.read(src); let n = 0;
  for (const node of doc.getRoot().listNodes()) {
    if (!node.getMesh()) continue;
    let nm = node.getName(), par = node; while (!DETAIL.test(nm) && (par = par.getParentNode ? par.getParentNode() : null)) nm = par.getName();
    const isDet = DETAIL.test(nm);
    if (isDet !== keepDetail) node.dispose(); else n++;
  }
  await doc.transform(prune());
  await io.write(out, doc); console.log(out, 'meshes', n);
}
