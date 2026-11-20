# Aurelia Island

**Android APK (full game, offline):** https://github.com/KingAtdhe/aurelia-island/releases/latest/download/aurelia-island.apk — every push to `main` builds a new one (`.github/workflows/apk.yml`, wrapper in `android/`).

An open-world driving game in the browser: a 12 km island with a city, harbour, countryside, mountain passes, desert and a racing circuit, driven in the **Vortex**. Built with three.js; every model and texture is made in Blender.

This repository is the full-texture version of the game: the map, terrain and car ship with their textures at full resolution.

## Play

- **Online:** after GitHub Pages is switched on (see below), the game runs at `https://kingatdhe.github.io/aurelia-island/`.
- **As an app on your phone:** open that link in Chrome (Android) or Safari (iPhone), then choose *Add to Home screen* / *Install app*. It opens full screen in landscape. After the first load the map stays on the phone, so later launches start fast and work offline.
- **Locally:** from this folder run `python3 -m http.server 8000` and open `http://localhost:8000`.

Controls: on-screen pedals and steering on a phone; arrow keys or WASD and Space (drift) on a computer. *Menu* has graphics quality, sound, auto gas and time of day (Day, Sunset, Night).

## Switching on GitHub Pages (one time)

Settings → Pages → *Build and deployment* → Source: **GitHub Actions**. The workflow in `.github/workflows/pages.yml` then publishes the game on every push to `main`.

## What is where

| Path | What it is |
| --- | --- |
| `index.html` | The game (three.js r128, single file) |
| `map/` | The island, split into binary parts with a small JSON manifest each (`islandc` world, `islanddc` detail, `florac` plants, `florakc` props) |
| `cars/` | The Vortex (170k triangles, original textures) |
| `data/` | Roads, heights, ground shading, plant and prop placements, clouds |
| `lib/` | three.js, glTF loader, meshopt decoder |
| `manifest.webmanifest`, `sw.js`, `icons/` | Installable-app files and offline cache |
| `source/` | Everything used to build it: Blender scripts (`source/blender`), packing and test tools (`source/game`), concept sheets (`source/art`), notes (`source/HANDOFF.md`) |

## Rebuilding the map

Requires Blender 5.3 as a Python module (`pip install bpy`) and the CC0 photo textures listed in `source/HANDOFF.md`.

```
cd source/blender && python3 isle_build.py -- out          # builds the island into source/blender/out
cd ../game && npm i @gltf-transform/core @gltf-transform/extensions @gltf-transform/functions @gltf-transform/cli meshoptimizer sharp
FULL=1 SITE=../.. python3 pack_app.py                      # full-texture map parts into map/ and data/
node car_opt.mjs vortex.glb /tmp/vortex_full.glb 1.0 4096 92   # the car: all triangles, original textures, meshopt
```

The car file is stored the same way as the map: `cars/vortex.json` (`{"bytes", "parts": 1, "fmt": "bin", "ext": "bin", "sizes"}`) next to `cars/vortex.p0.bin`, the GLB itself.

When the map changes, bump `VERSION` in `sw.js` so installed copies fetch the new files.
