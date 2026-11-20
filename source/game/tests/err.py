pg.wait_for_function('window.__detail === 1', timeout=300000)
print(pg.evaluate('''()=>{const bad=[];__game.scene.traverse(o=>{if(!o.isMesh)return;const g=o.geometry;for(const k in g.attributes){if(!g.attributes[k])bad.push(o.name+':'+k)}if(g.index===undefined)bad.push(o.name+':idx?');if(o.isInstancedMesh&&!o.instanceMatrix)bad.push(o.name+':im');});return JSON.stringify(bad.slice(0,20))}'''))
print(pg.evaluate('''()=>{const out=[];__game.scene.traverse(o=>{if(o.isInstancedMesh&&o.instanceColor===null&&o.material.vertexColors)out.push(o.name)});return out.length}'''))
