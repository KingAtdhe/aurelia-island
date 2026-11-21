// Keeps the game and its map on the phone after the first load, so later launches start fast and work offline.
// Bump VERSION whenever the map or the game changes, so phones fetch the new files.
const VERSION = 'aurelia-v15';
self.addEventListener('install', e => { self.skipWaiting(); e.waitUntil(caches.open(VERSION).then(c => c.addAll(['./', 'index.html', 'manifest.webmanifest']))); });
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const r = e.request; if (r.method !== 'GET' || new URL(r.url).origin !== location.origin) return;
  const fresh = /index\.html$|\/$|\.json$/.test(new URL(r.url).pathname) && !/\/(map|cars)\//.test(r.url);   // the page and small data: network first
  e.respondWith(fresh
    ? fetch(r).then(res => { const c = res.clone(); caches.open(VERSION).then(k => k.put(r, c)); return res; }).catch(() => caches.match(r))
    : caches.match(r).then(hit => hit || fetch(r).then(res => { if (res.ok) { const c = res.clone(); caches.open(VERSION).then(k => k.put(r, c)); } return res; })));
});
