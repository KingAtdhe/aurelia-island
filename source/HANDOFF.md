# Aurelia Island — handoff (19 Nov 2026)

Live game: https://claude.ai/artifact/A64G2MYi864WTYwo8t6MJo (artifact slug 4996f9a8-f551-47b5-ba73-c6bbc28314b0, last version 1795155785-a346).
The artifact holds the full packed map; this zip holds the source to rebuild it.

## Session setup (fresh container)
- photo/*.raw are not in the zip: clone papyszoo/cc0-public-domain-textures (blob filter, checkout the 34 folders used), build
  BinomialLLC/basis_universal, run tools/decode_photo.sh. game/site/lib + data/clouds.png + cars/ come from the live artifact (read_file).
- pack_map.py reads /home/claude/isle/out: symlink /home/claude/isle -> blender. npm i @gltf-transform/{core,extensions,functions,cli} meshoptimizer in game/.
- Publish in batches under 64 MiB per publish_files call (patch mode).

## Rebuild
- Blender 5.3 via `pip install bpy`. Photo textures: CC0 ambientCG via github papyszoo/cc0-public-domain-textures (KTX2 decoded to blender/photo/*.raw).
- `python3 isle_build.py -- out` (~20–35 min) -> out/aurelia_island.blend + glb parts
- `cd game && python3 pack_map.py` -> site/map/*c.json (meshopt, JPEG, base64 parts). Publish index.html, data/*, map/*c.json and map/*c.p*.wasm (256 MiB artifact limit; swap one asset per call: new parts + manifest + remove old).
- Screenshot tests: `python3 test.py <name>` (tests/*.py, headless Chrome, Medium quality).

## Done
- Game (index.html, three r128): bloom/grade/speed blur/sun flare post pass, region colour moods, wind sway, facade grime,
  wall-base darkening, worn markings, haze fog curve, interior-mapped windows, night lights (traffic headlights, lamp pools),
  traffic lights driving signal lamps, traffic queueing/turning, 5 modelled traffic cars (isle_traffic.py) + parked cars, walkers.
- Blender: city blocks (isle_city), hero buildings A–D x3 variants from approved concept sheets (isle_hero.py, 44 placed),
  shared shop-sign atlas, neon/billboards, street clutter, gutters/drains, photo far facades, brick variety, clouds.
- Rated ~8.7/10 vs CarX ~9.

## Workflow agreed with Saba
Art sheet (professional concept style: Blender model in lit street scene, Cycles, graded, laid out) -> her approval -> model -> build into map.
Concept 01 (hero buildings) and 02 (night/signage): APPROVED and built.
Concept 03 (street furniture, isle_props_hq.py): APPROVED 19 Nov and BUILT. Registered as <name>_hq; isle_props_hq.apply() swaps kit
placements in the old town (city outside the glass-tower core, core() < 0.5); heritage lamps placed directly in isle_stage2 lamp();
bollards at old-town corners, drinking fountains among planters. Live version 1795085653-36b6.
Concept 04 (trees & vegetation): APPROVED 19 Nov and BUILT (live version 1795090620-4c27). isle_flora.HQMAP routes the old species
names to isle_trees_hq (spruce/spruce_b/pine -> Norway spruce, oak/oak_b, birch, fruit -> olive, palm -> date palm, palm_b -> stone pine,
cypress, bush -> laurel, cactus -> prickly pear, cactus_b -> agave, grass/flowers -> new clumps); map LOD0 = game-weight version (lod=2),
LOD1 = far (lod=1); lod=0 is the hero version for renders. isle_ground: city broadleaves -> plane/plane_b, forest undergrowth bushes -> fern,
half the garden bushes -> oleander. Material LeavesHQ + Bark_<kind>; game treats /^Leaves/ like Leaves. Impostors re-rendered
(flora_impostors.py, brightness-normalised); card ratios ASP = [0.66, 0.66, 1.3, 0.5, 1.0, 0.9] in game and renderer.
Open: spruce_snow is still the old model; clipped hedge not placed anywhere yet; oak game version ~10k tris.

Concept 05 (countryside, village, farms): APPROVED 19 Nov and BUILT (live version 1795104478-0411). isle_country_hq registered in
isle_ground with CQ.FOOT footprints; isle_features: house() now picks cottage/cottage_b (small) and farmhouse/village_row (village core
within 120 m of 610,-850); each farm (5 sites) = barn_hq + silos + tractor + hay_shed + hay_field + walls_fences + a farmhouse; Summit
Lodge = winery_hq; 6 vineyard plots of 6 blocks round the village; 3 farm stands on Farm Road / Orchard Lane. Game regex groups the
new buildings as 'bld', farm_stand/tractor as 'tiny'. Placed: 26 cottages, 21 farmhouses, 2 village rows, 36 vineyard blocks.

Concept 06 (harbour & coast): APPROVED 19 Nov and BUILT (live version 1795113745-3a56). isle_coast_hq registered in isle_ground.
Marina: the three piers were partly on land, so isle_features now slides them to the nearest open water (C.marina_shift, came out -84, -30);
12 timber jetty segments, 14 sail + 6 motor yachts (marina and offshore). Fishing village: 6 modelled fishing boats along the pier.
Beaches (isle_stage11.coast): beach_set / rowing_boat / lifeguard / beach_bar facing the sea (35 / 15 / 7 / 5). Harbour kiosk on the quay,
2 breakwaters in open water. Still primitive: cruise ship, cargo ship, fishing-village pier; promenade not placed yet.

Concept 07 (mountains, desert, roadside): APPROVED 19 Nov and BUILT (live version 1795118662-635f). isle_wild_hq registered in isle_ground.
Rocks: isle_flora rock/rock_b/rock_c/sandstone/sandstone_spire now use isle_wild_hq.rock_mb (fractured boulders, strata on sandstone).
Guardrail: W-beam profile + blockouts + reflectors in the isle_build rib. Tunnels: tunnel_portal_5/6/7 kit (arch follows the road tunnel
curve Rw = hw + 1.3, Ht = 7) replaces portal_masonry (6 portals). Lookouts (isle_stage11) use the lookout kit (5). isle_stage11.wild_props:
3 windpumps, 2 desert stops, 2 mountain sign sets. Not placed yet: cliff faces on road cuts, scree fans, parapets, catch fences.

## Next categories (each: sheet -> approval -> build)
04 trees & vegetation · 05 countryside/village/farms · 06 harbour & coast · 07 mountains/desert/roadside (rocks, cliffs, guardrails, tunnels)
· 08 roads & junctions · 09 landmarks (church, lighthouse, stadium, petrol station, windmill).


## Concept 08: roads and junctions (APPROVED and built, live 1795126497-d3b8)
- blender/isle_roads_hq.py: 12 road vignettes registered as road_<name> (highway, country_road, hairpin, city_crossing, setts_street, roundabout, junction, bridge_deck, roadworks, bus_layby, car_park, gravel_track); materials() adds asphalt (Asphalt010), setts (PavingStones070), gravel (Gravel022), grassg (Grass004), low specular so flat surfaces don't mirror the sky.
- blender/sheet08_render.py renders them (ground dropped to -0.06 to avoid z-fighting with road tops; scatter hidden under the vignette footprint). art/sheet08.py composes the sheet; game/tests/roadcur.py takes the current-road strip (SPOTS env).
- Built: isle_roads_build.py (called after S7.roads_extra): highway rumble strips + cat's eyes, 737 marker posts, chevron boards on bends tighter than R90,
  gravel tracks with wheel ruts and a grass crown, bridge expansion joints, 4 road-works sites on the Ring verge (barriers collide via C.obst).
  Old-town streets (HQ.oldtown) emit as RoadSetts (PavingStones070). Roundabouts: rk_island_<ri*10> kit replaces the primitive island; give-way
  double dashes and triangles where roads meet a roundabout (stage7). Map kit pieces: isle_roads_hq.register_kit() (rk_*), called in place_flora.
- Test: game/tests/roadnew.py, roadnew2.py. Total published ~245 MiB (under 256).
- Next: sheet 09 landmarks (church, lighthouse, stadium, petrol station, windmill).

## Concept 09: landmarks (APPROVED and built, live 1795155785-a346)
- blender/isle_landmarks_hq.py: church_hq, lighthouse_hq, windmill_hq + windmill_sails_hq (same hub at (0, -4.3, 18.2), spins), fuel_station_hq
  (brand atlas: AURELIA wordmark, price board, shop, car wash), stadium_hq (a=105, b=84). Same frames/footprints as isle_landmarks, so the
  build swaps the LMK.* calls in isle_features / isle_stage3. register(M) adds lm_* (plus limestone material) for the sheet renders.
- blender/sheet09_render.py (DETAIL env for close-up cameras), art/sheet09.py, game/tests/lmcur.py (LMS env: x,z,distance per shot).
- Known: church limestone reads grey in the sheet light; warm it up during the build.
- Built: isle_features / isle_stage3 call isle_landmarks_hq (kit_mats() adds limestone + brand atlas to the kit materials); the lighthouse's
  separate house is gone (cottage is in the model); fuel station built with wash=False (the bay would leave the platform).
- Map parts are now raw binary: pack_map.py writes <name>.json manifest {bytes, parts, fmt:'bin', sizes} + <name>.pK.wasm (12 MiB each).
  The artifact host refuses .bin/.glb; .wasm is accepted and served byte-exact. index.html getBin reads both formats (PACK_B64=1 for old).
  Live total ~191 MiB of 256.

## Look pass (20 Nov 2026, live 1795157022-54b3)
- index.html: three times of day (Day / Sunset / Night, stored as aurelia_tod, default Sunset). buildEnv(warm) makes the reflection map per
  preset; sky shader uWarm; post grade 'dusk'. SUN_DAY / SUN_DUSK set SUND. game/tests/look.py takes 6 fixed views (PFX, Q, JS env).
- Diagnosis vs CarX (biggest first): player car is a low-poly blob (Vortex/GT not in this workspace: car_vortex.py lives in
  gauntlet-handoff.zip); traffic cars are blobs; city street level flat (plain glass boxes, black ground floors, empty pavements);
  terrain and trees in shadow go near black; mountain rocks read as scattered black lumps.

## Concept 10: city street level (sheet sent, awaiting approval)
- blender/isle_shops_hq.py: storefront(K, M, F, a, b, gf, rng, door, shop) (same frame convention as isle_city.shopfront, meant to replace it),
  shutter(), podium() for glass-tower ground floors; atlases: 16 original shop fascias (sign_atlas) and 4 painted interiors (interior_atlas);
  materials KitShopSign, KitShopInterior (emissive; the game should raise it at night), KitShopGlass (tinted, transparent).
- blender/sheet10_render.py, art/sheet10.py. Build plan after approval: isle_city.building() and tower_base() call these; index.html treats
  KitShopInterior like lit rooms (brighter at night) and KitShopGlass as transparent.

## Vortex in the game (20 Nov 2026, live 1795162993-b972)
- Saba sent vortex_sale_pack.zip (vortex.glb 170k tris, 40 MB). game/car_opt.mjs makes the game copy: drops lightmap UVs, tangents and
  COLOR_1, welds, simplifies to 0.75, JPEG textures at 1024, meshopt -> 2.7 MB at site/cars/vortex.json + vortex.p0.wasm.
- index.html: fitCar(obj, noseNegZ) turns the -Z nose to +Z; sale-pack wheels found by name (Front_Left..., Steer_Front_* for steering,
  spin sign flipped for the turned model); chase camera closer (7.0 m, 2.5 m up).

## Concept 11: touge kit (sheet sent, awaiting approval; concept 10 also still awaiting)
- Saba pointed at CarX's "IDA Hakone Nanamagiri Touge" map. blender/isle_touge_hq.py: lattice_slope, shotcrete_cut, retaining_wall, u_ditch,
  curve_mirror, guard_pipe, road_light, spillway, delineators, road scenes touge_straight / touge_hairpin; trees are flora instances
  (TREES dict filled by the scenes). sheet11_render.py, art/sheet11.py.
- App repo: github.com/KingAtdhe/aurelia-island (full textures, PWA, Pages workflow; pack_app.py FULL=1 SITE=<repo>)

## Touge and storefronts built (20 Nov 2026; artifact 1795182802-9a82, GitHub 2f30490)
- isle_roads_build.touge(): on the 4 passes, where the ground 31 m out is >4 m above the road, a retaining wall + U-ditch at the edge and
  a built cut face (TougeLattice cutout / TougeShotcrete) rising to the hill's height within 10 m, then a grassed terrace (TougeTerrace)
  with conifers; curve mirrors + sodium lights at bends tighter than R45; ~3,100 conifers along the open sides; double yellow line;
  white guard pipe instead of W-beam on the passes. (Built ~2.3 km of cut.)
- Storefronts are instanced prefabs: isle_city.building()/tower_base() call isle_shops_hq.place() which records K.shops; emit_model()
  turns them into KP.KIT 'shop_<n>_<width>' (16 shops + shutter, widths 4-7 m); register_kit in place_flora. 1,542 placed.
  The bay is closed with ashlar either side of the prefab. NOSHOPS=1 env builds the old shopfronts.
- Memory: the build peaks ~5.8 GB of the ~6 GB cgroup here. Do not load kit materials (KP.mats()) before place_flora, and keep
  heavy per-building geometry out of the city Parts (use prefabs/instances).

## Traffic cars, second generation: NOT shipped (20 Nov 2026)
- blender/isle_traffic_hq.py + sheet12_render.py: lofted bodies with material zones on the cage (glass, pillars, lamp bands, grille),
  boolean arches, five-spoke wheels, ~29k tris. Tested three rounds; the shapes still read dated and the fronts are heavy black zones,
  so no sheet was sent (Saba's rule: no unfinished cars). Not used by the game; the game still uses isle_traffic (tcar_a..e).
- Recommended route: model each traffic car as its own script the way car_vortex.py was made (reference picture, several passes),
  then export game copies with game/car_opt.mjs and place them as tcar_* props.

## Wet roads (Nov 20)
- index.html: Options → "Road: Auto/Dry/Wet" (store 'wet'; Auto = wet at night). Asphalt/Setts materials kept in ROADM; applyWet() darkens them, lowers roughness, flattens normals (no glitter).
- Road pixels write alpha 0.25 (onBeforeCompile); mComp `wet` uniform smears the bloom buffer down over those pixels for light reflections (capped at 0.45, faded at the screen bottom).
- Puddles get roughness 0.3 at night to avoid hard headlight hotspots. App sw.js is now aurelia-v3.

## Vortex mesh audit (Nov 20)
- Tools in /home/claude/meshcheck: mesh_audit.py (transforms, topology, UVs, textures), island_audit.py (faces only ever seen from behind, per connected part), patch_glb.py (reverses winding + normals + tangent.w on listed parts; gives shared index lists a private copy), fix_blend.py (same on the .blend, custom normals kept), fbx_export.py.
- Found and fixed: front tyres inside-out, left brake-disc hole inserts, exhaust surrounds, door jamb/seal pieces, taillight housing, bumper carbon inserts, cabin tub. Positions/UVs/transforms/materials byte-identical.
- Game copies rebuilt: browser car_opt 0.75 1024 82, app car_opt 1 4096 92. fitCar keeps sale-pack cars at real size (no 4.6 m rescale).
- Fixed pack: /home/claude/vortex_sale_pack_fixed.zip

## Glitch pass (Nov 21)
- Merged far blocks: quantized attributes are de-normalised (QN/rd) — this caused sky triangles, grey slabs, speckled leaves.
- Colliders generated in-game from flora data (floraColliders): poles/lamps/signals = 0.22 m circle, trees = trunk circle, rocks/parked cars/kiosks = boxes or circles from bbox, KNOCK list = knock-away (hidden + group rebuilt). SOFT list never collides (bushes, shop fronts, tunnels/portals/bridges, hay field, jetty). No box is ever placed across a carriageway.
- Car collision uses 3 circles (nose/middle/tail, r 1.0).
- r.lim per road side: touge cut retaining walls (hw+0.25) and guard rails on the drop side (hw+1.6), computed from the heightmap with the builder's rules.
- Camera kept inside the road corridor when the car is on the road. Cam 3 is now a bumper camera. Car paint keeps a dim dusk env map at night (carEnv).
- Traffic: gives way to crossing cars in junctions, only turns into clear streets (4 min sim: 0 overlaps, no jams).
- isle_features: apex grandstands skipped when they would overlap a road (one sat on Pit Access). Map rebuilt and republished.
- Test scripts: tests/sim3.py (autopilot physics on every road), coll.py, hit.py, wall.py, rail.py, traffic2.py, walk.py, ui.py, sweep.py.

## Vehicle dynamics and drifting (Nov 21)
- physics() now calls drive(): two-axle model, 4 substeps per 120 Hz fixed step, world-frame integration. Left = (cos h, -sin h); heading grows turning left.
- Tyres: lat = sin(C*atan(B*alpha)), front B 11.5 / rear Br 14.5, C 1.42, mu 1.15 x muF 0.96 / muR 1.10 (stable, slightly understeering base), relaxation length 0.45 m.
- Friction circle on the rear with drive force; wheelspin/lock keeps 60% side grip. Load transfer from filtered ax. Downforce, drag, rolling resistance per surface (MU/RRS tables).
- Engine torque curve (peak 660 Nm ~5900 rpm, limiter 8100), 6-speed auto, holds gear when sideways; ABS front/rear bias 0.63; handbrake locks rear; reverse by holding brake.
- Steering: speed-sensitive range (~5 deg at 100 km/h), extra drift lock (to 50 deg) only for counter-steer while the rear slides. Steering assist (option, default on): wheels follow travel when sliding, yaw-rate limiter, throttle feathering around 30-40 deg.
- Traction control for grip driving (car.drift timer): released by handbrake, big angle, or full lock + full throttle (power oversteer).
- Measured (tests/lab.py, drift.py, edge.py): 0-100 3.9 s, 0-200 9.5 s, top ~238 km/h, 100-0 37 m; steady drift ~42 deg on throttle; transitions without spin; release recovers in ~1.2 s.
- FX: smoke/dust points + skid ribbons from car.slipR. DS: drift scoring (12-100 deg, >25 km/h, combo up to x5, crash/spin loses). Touge Drift mode on Summit Pass. HUD gear + RPM. Audio from rpm + tyre squeal noise.
- Camera: follows travel direction in drifts; pulled in front of buildings. Gamepad: left stick, RT/LT, A/X handbrake, Y camera, Start menu. Menu now has Resume.
- Leaf atlas is painted very dark (sRGB ~22,33,9): LEAF_LIFT shader curve on all leaf/card materials.

## Progression (Nov 21)
- PROG (store 'prog'): credits cr, upgrade levels eng/tyre/kit/wt, paint index + owned list. applyUpgrades() sets VEH.tq (torque factor), VEH.mu, VEH.lockD (drift lock), VEH.m (Iz scales with mass).
- Credits: banked drift points /10, circuit finish 1500, ring 2500, best lap 400, touge 600 + score/12, landmark 250.
- Garage overlay from the menu; paint replaces the solid-red livery map with a colour (Factory restores the map).
- Steering option: Buttons / Tilt / Tilt (reversed); tilt zeroes at start of each run, ±24° full lock, 2° dead zone.
- Aurelia GT (cars/aurelia_gt.json) is a 6k-triangle placeholder — not offered in the garage. A second real car needs modelling.

## Second car: Calder GT (Nov 21)
- Source: Saba's calder-gt-sale.zip. Audit: transforms, UVs, textures fine; 43 materials. Fixed only: 740 zero-area/duplicate faces in the .blend (2,522 sliver + 33 same-facing duplicate triangles in the GLB): badge, console, dashboard, door panels, headlights, mirrors, interior tub, steering wheel, wheels. No vertex moved. Grille faces reversed but its material is double-sided, left as is. Fixed pack: /home/claude/calder_fixed (blend, glb, fbx without the hidden COL_ proxies).
- Scripts: meshcheck/clean_glb.py (drops zero-area and same-facing duplicate triangles), clean_blend.py, calder_export.py. car_opt.mjs now takes DROP= (attributes to strip) and PLAIN_PAINT= (material whose base texture is removed so the game can paint it).
- Game: CARS table (vortex, calder) with per-car VEH (mass, axle split, gears, torque peak). PROG now {cr, car, cars[], up:{id:{eng,tyre,kit,wt,paint,owned}}}; old saves migrate to up.vortex. Garage has a car row (buy 25,000 / switch). fitCar accepts Wheel_(Front|Rear)_(Left|Right) under Steer_Front_*, wheel axis 'z' with sign −1. KHR transmission glass shown as transparent tinted glass.
- Calder bench: 0–100 4.33 s, 0–200 11.7 s, 100–0 38.1 m, drifts hold ~40°, transitions without spin. Tests: tests/calder.py, calder2.py, lab_c.py, drift_c.py.

## Traffic car 01: Mira compact hatchback (Nov 21)
- Sheet approved ("Continue"): art/traffic_01_mira_design_sheet.jpg (blender/traffic/sheet_mira.py draws it).
- Model pipeline (blender/traffic/): mira_sdf.py = body as a signed distance field (side + plan silhouettes from the sheet, smooth intersection,
  tumblehome, crowns, shoulder crease, door sculpt, arches with lip). build_body.py: marching cubes (12 mm) → pre-decimate → zone cuts along exact
  isolines (meshcut.py; zones in mira_zones.py: clad, arch liners, glass, pillars, lamps, LED, tail, band, grille, intake…) → decimate with zone borders
  protected (vertex group, invert) → project back onto the field → lamp/grille/intake recesses with walls. build_parts.py: gap lines as surface
  ribbons, wheels (lathe tyre with grooves, five twin-spoke rim, disc, caliper), mirrors, handles, spoiler, aerial, slats, badge, plates, interior,
  far LOD from a coarse field surface with cut zones; exports /tmp/mira.glb (LOD0 = Mira_Body + Mira_Parts, LOD1 = Mira_Far).
  patch_normals.py writes exact field normals into the body (smooth shading on a light mesh). shoot.py + view/ render it in three.js.
- Counts: near 26.8k body + 12.2k parts, far 3.9k. Game: cars/mira (car_opt 1 512 82). index.html TMODELS/loadTraffic() replaces FLO.lib.prop_tcar_a
  (traffic and parked hatchbacks) before addKit; near model within 45 m on phones, 70 m otherwise. 'Paint' takes the instance colour; 'Glass' is
  see-through. __camHold freezes the game camera for photo tests (tests/mira.py, mira2.py).
- Next traffic sheets: 02 saloon, 03 SUV, 04 van, 05 taxi (saloon livery). Reuse the pipeline with new silhouettes and zones.

## Traffic car 02: Vela family saloon (Nov 21) — sheet sent, awaiting approval
- art/traffic_02_vela_design_sheet.jpg drawn by blender/traffic/sheet_saloon.py (imports helpers from sheet_mira.py).
- 4,700 × 1,840 × 1,450, wheelbase 2,800, 17" 215/55, R 0.335, axles at 0.93 / 3.73 from the nose. Three-box, six-light glasshouse with
  satin chrome DLO, sharp feature line through flush chrome handles, slim headlamps joined by a lit grille bar, full-width tail bar,
  lip spoiler, ten-spoke two-tone alloy. Paints: slate blue, burgundy, moon silver, midnight, sandstone, pine green. Taxi 05 = Vela in livery.
- After approval: vela_sdf.py / vela_zones.py on the Mira pipeline (build_body, build_parts), car_opt 1 512 82, replace prop_tcar_b in TMODELS.
- APPROVED ("Continue", 21 Nov) and BUILT. blender/traffic: vela_sdf.py, vela_zones.py (zones, recess GROUPS, GAPS with explicit side, FUEL),
  vela_parts.py (generic parts script: CAR env; ten-spoke two-tone wheels with lug nuts, flush chrome handles, slim lip spoiler, DRL strips,
  slats + intake fins, V badge, chrome pipe trims, interior). build_body.py and patch_normals.py now take CAR=mira|vela (default mira).
  Build: CAR=vela python3 build_body.py && CAR=vela FPRE=0.05 python3 vela_parts.py && CAR=vela python3 patch_normals.py /tmp/vela.glb /tmp/vela_n.glb
  Far LOD (new method): field surface at 24 mm, pre-decimated evenly, cut along the zone curves, each piece labelled by the closest point
  on the finished near body (BVH), so no saw-teeth where zone masks switch. Counts: body 32.7k, parts 15.4k, far 9.0k.
  Game: car_opt 1 512 82 -> 0.58 MB, site/cars/vela.json + p0.wasm; index.html TMODELS adds prop_tcar_b: 'cars/vela' (old saloon kind).
  Live artifact version 1795286482-5241. NOT yet in the GitHub repo/APK (push access was refused this session): copy
  game/app/cars/vela.json + vela.p0.bin and the TMODELS line into KingAtdhe/aurelia-island.
- Viewer shadows show dark slivers on the doors (shadow-map artefact, gone with ?ns=1); geometry is clean.
- Next: traffic sheet 03 SUV (prop_tcar_d), then 04 van (tcar_c), 05 taxi = Vela + livery (tcar_e).

## Traffic car fix pass (21 Nov, after Saba: "fix the cars, what is this?")
- Both Vela and Mira rebuilt; live artifact 1795288530-f1d7 (cars/vela + cars/mira). APK copies in game/app/cars (repo push still not done).
- Glass is single-sided (backface culling) and darker (alpha 0.74): no more hatching where both window layers overlapped. Interior darker,
  Vela seats rounded (bevelled) in dark leather; rear headrests smaller. Headlamp housing dark smoked chrome instead of flat grey.
- Mirrors: shaped housing (flat glass face, tapered tip) + glass + slim arm, on both cars. Plates carry printed text (AU · V3LA / AU · M1RA,
  PlateText material with a packed PNG); game copy needs KEEPATTR=1 node car_opt.mjs ... (prune otherwise drops the plate UVs).
- Vela light lines (headlamp DRL, tail bars, grille bar, reverse lamps, reflectors) are separate parts laid on the surface, not body zones:
  clean edges instead of saw-teeth. Wheel flange no longer stands proud of the spokes.
- Viewer (blender/traffic/view): soft shadows, views nose/wing/quarter, ?ns=1 no shadows, ?nsm=<mats> exclude materials from shadow casting.
  The dark door patches in the first renders were the mirror's hard shadow, not geometry.
- Known still: soft fold on the Vela rear quarter below the C-pillar; Mira body untouched (only materials, mirrors, plates).

## Phone performance pass (21 Nov, after Saba's video: laggy)
- Measured with tests in a mobile profile (aurelia_mob=1, Medium): draws per frame city 1045 -> 718, coast road 525 (+240 shadow) -> 352 (+91),
  forest 428 -> 265; city triangles 1.6M -> 1.1M.
- mergeCar(): the player car (sale-pack Vortex/Calder, ~190 meshes) is joined by material at load; wheels and steering pivots stay separate
  (~31 meshes). Quantized attributes are de-normalised while merging.
- Phones: tiny/solid props do not cast shadows below High; far grass layer only on High; bFar 0.9 x far, sFar 0.22 x far; at most 3 new
  flora groups built per tick (re-check every 60 ms while some are pending) so new ground does not stall a frame; renderer.compile after
  the detail map loads (no shader hitches on first sight).
- Leaves (noFlip materials) dissolve within ~2-4.5 m of the camera: no screen-filling leaf cards when passing a tree.
- Not changed: Vortex diffuser fins (long, read as spikes from the chase camera) - Saba's design, ask before shortening.

## Look pass toward CarX (21 Nov, "do all the things that get us closer to CarX")
- look2Ground (Terrain*, chained after the shade patch): world-space value noise -> lush/dry/worn patches on grass ground, fine grain
  close up, forest floor lifted; sky-fill floor (outgoingLight += albedo * 0.13-0.19, scaled down at night via NIGHTU).
- look2Leaves (Leaves*, after noFlip): canopy darker at the bottom/inside, brighter crown, per-tree tint from the instance position; sky fill.
- Baked shade map at half strength (live shadows already darken). Hemi: day 0.55, dusk 0.7, night 0.2. Terrain/leaf envMapIntensity 0.8.
- Reflection env (buildEnv): 96x48 dome with a broken tree line / hills band and darker ground at the horizon.
- Bloom 0.42 -> 0.34, sun glow softer. Off-road: RRS grass 10, sand 13, snow 6 (was 4/6/3); drift points 0 on grass/sand/snow, half on dirt.
- r128 here has no output_fragment chunk: anchor on 'gl_FragColor = vec4( outgoingLight, diffuseColor.a );'.
- Perf unchanged (phone Medium: city 721 draws, coast 363, forest 259). Live artifact 1795xxxxxx (see artifact history).
- Not done / needs assets: dense close-up grass, hand-made rocks and ground textures, real-time car reflections (too expensive on phones).

## Tripo props (22 Nov 2026)
Saba made 12 models in Tripo (Smart Mesh, untextured FBX) and 47 textures in ChatGPT. Inspected all 12: clean (no doubles/loose),
open shells; DO NOT recalc normals (flips open shells). Pipeline in source/tripo:
- tlib.py: load FBX at real size; procedural per-part materials from the ChatGPT tiles (box projection); bake() decimates to the game
  budget, smart-UVs, and bakes colour+AO+normal from the high mesh onto the low one (selected-to-active).
- rocks.py (boulder, slab, stones, cliff, corner), bld.py (cafe, house, barn, lighthouse, petrol, bridge, pine) classify faces by island
  size/position/normal into parts (`-- <name> debug` renders the part colours).
- lods.py sets sizes and names T_<species>_LOD0; tprops_pack.mjs merges, makes LOD1 with meshopt simplify, textures 1024 colour / 512 normal.
- Game: props/tprops (loadTProps after traffic cars). Replaces rock, rock_b, rock_c, prop_barn_hq and prop_farmhouse (moved to
  prop_house_t_village), hides Landmark_Lighthouse for the new one, and tripoPlace() adds houses, cafe, barn, petrol canopy, slabs and
  cliffs beside Peninsula Road / Lighthouse Road / West Avenue / Ring in the Coastal Highway region. No per-instance tint (TPROPS).
- Not placed yet: the bridge (no free crossing) and the pine (Tripo gave it broad fan leaves, not needles).

## Godot: the whole island (24 Nov 2026)
The Godot game (godot/) now has all of Aurelia Island, cut from the web game's map so it matches the approved art. Tools in
source/godot_tools (run with the unpacked map: reassemble map/islandc*.bin etc. and unpack with gltf-transform dequantize, see
glbcut.py header):
- export_chunks.py islandc_raw.glb islanddc_raw.glb godot/assets/island -> chunks/b_* (ground, roads, water edge, far buildings),
  bf_* (landmarks, tower crowns, wind turbines: always loaded), d_* (close-up buildings and street kit, streamed), index.json.
  Every mesh goes to the 400 m cell of its box centre. Pictures go once to island/tex (tex/_src.json maps original md5 -> file).
- export_flora.py florac_raw florakc_raw tprops_raw <repo> godot/assets/island -> flora_{flora,kit,tprops}.glb (S_<species>_LOD0/1)
  and flora.bin/json (x y z scale yaw r g b). data/flora.json everywhere, the coast slice's own set (coast_flora.json: Tripo houses,
  slabs, cliff) inside the coast rectangle; farmhouses -> Tripo village house; two Tripo cafes placed beside the coast roads; Tripo trees
  replace pine/oak/plane/fruit/cypress; DROP list as in the web game.
- gen_coll.py <repo> -> island/coll.json: world obstacles/circles + every flora collider (floraColliders rules) + road side limits.
- shrink_tex.py + tex_imports.py: textures capped at 1024 colour / 512 normal+ORM, VRAM compressed.
- bake_island.py (TILE=i,j, 4 x 3 tiles, Cycles top-down sun / no-shadow sun / sky) + combine_island.py -> bake_island.png
  (R sun, G sky, 4096 x 2868 over the island) and bake_sun.bin (2048 x 1434 sun map read on the CPU). Bridges are visible to the bake
  camera (decks), buildings/props only cast. Tunnel roads are painted dark after the render.
Game side: scripts/island.gd (base always in, detail streamed on a thread within 950 m, dropped past 1250 m, at most one chunk put in
per frame; draw ranges per group), flora.gd (250 m patches built near the car, buildings everywhere; impostor tree cards from the web
game's atlas beyond 200 m), tunnels.gd (bore split out of the Bridges meshes: tiles, vault, lamp rows, light pools; eyes adjust
inside), traffic on every paved road kept 140-520 m round the player, cars on render layer 2 lit by a car sun dimmed by bake_sun.bin.
Races: coast, peninsula, lighthouse + Summit Pass, Eagle Descent, Desert Dash, Serpentine, Aurelia Grand Prix (2 laps; roundabout
arcs instead of the fountain in the middle). Menu: RACES and TRAVEL (9 regions). Test tools: TOUR="Road:frac,..." (screenshots after
streaming, prints draws/prims and the slowest chunk put-ins), RACETEST=<id> prints STREAM worst ms at the end.

## Godot: career, garage and prize money (24 Nov 2026)
scripts/progress.gd (user://progress.cfg; CAREERSAVE=<path> for tests): credits (new career starts with 5,000), cars owned
(Calder GT 25,000), per-car upgrades (engine +8/16/25% torque, tyres +4/8% grip, drift kit lock, weight -50/-100 kg; same table
as the web game) and paint (9 colours, 1,500 each, kept once bought). Race purse 1,200 + 900 per race in the list (Grand Prix x2),
paid 100/60/35/12% by place; a podium opens the next race (first three always open, old podiums count). Landmarks found in free
roam pay 250. Menu: BUY on unowned cars, GARAGE page, locked races greyed with the reason. Race results show the credits won.

## Godot: graphics glitch pass (24 Nov 2026)
- Rivers: source/godot_tools/fix_rivers.py (run after export_chunks.py) settles River_* water onto the ground and dips it under
  roads (Ring crossing at x -1694 had the river running over the deck). Edits the exported b_ chunks in place.
- Decals (Markings, RoadDecals*, Skids, Puddles, ContactAO, ShoreFoam): shaders/decal.gdshader pulls them 8 mm toward the camera
  (no flicker against the road) and shades them with the island bake like the road under them.
- Windows (WindowGlass, KitWindow, HeroCurtain): shaders/interior.gdshader, the web game's traced rooms behind the glass.
- Road: sunlit asphalt was near white; albedo capped and desaturated in road.gdshader. Grass ring blends to ground green with distance.
- Wind turbines: rotors spin (island.setup_spinners, all world.json spinners); past 400 m a plain mast stands in for the tower,
  which streams with the detail Shapes (420 m), so blades never hang in the sky.
- Shop prefabs (prop_shop_*): source/godot_tools/export_shops.py (after fix_podium.py) moves the 234 that stood 1-6 m behind a
  podium wall out onto it and merges all 1,542 per 100 m cell (LOD1) into s_<cx>_<cz>.glb chunks (group Shops, drawn to 280 m).
- Test hooks: TOUR spot "P:x:y:z:heading[:cx;cy;cz]" (free camera), HIDEGRP=Group,Group hides map groups, LODT=mesh LOD threshold.
- City ground floors: source/godot_tools/fix_podium.py (after export_chunks.py) moves the near-black podium panels of the city
  Structures into a WindowGlass primitive, drawn as glass with rooms behind it instead of blank grey slabs.

## Godot: graphics settings (25 Nov 2026)
- scripts/gfx.gd (class Gfx): LOW / MEDIUM / HIGH, button on the start screen, saved in user://settings.cfg (phones start on
  MEDIUM, desktop on HIGH; GFX=LOW|MEDIUM|HIGH env overrides for tests). Sets render scale (0.7/0.85/1), MSAA, mesh LOD
  threshold, sun shadows (off / 1 split 45 m / 2 splits 60 m), bloom, haze and camera reach (1500/2200/3000 m), draw distances
  of every map group and flora kind (x0.6/0.8/1), modelled grass (off/30/40 m) and traffic cars (8/11/14, at start).
- source/godot_tools/merge_hd.py (after export_chunks/fix_podium): the HD city buildings are merged per 200 m quarter and
  material in the detail chunks: 1274 -> 479 primitives. A city street: 1440 -> 1091 draws on HIGH, 890 MEDIUM, 679 LOW.
- Test hook: DRAWSPLIT=1 with TOUR prints the draw calls per map group.
- Order after a fresh export_chunks.py: fix_rivers.py, fix_podium.py, merge_hd.py, export_shops.py.

## Godot: time of day (25 Nov 2026)
- scripts/tod.gd (class Tod): DAY / SUNSET / NIGHT, TIME button on the start screen, saved in user://settings.cfg (TOD env for
  tests). Skies: assets/sky.png (day), sky_sunset.png and sky_night.png from source/godot_tools/sky_tod.py (bpy + numpy).
  Sets sun/moon direction and colour (car_sun too), ambient (night: moonlit blue fill, no sky contribution), haze, exposure.
- Global shader values (project.godot [shader_globals]): tod_sunbake fades the baked sun shadows in terrain/road/decal/grass
  (1 / 0.3 / 0), tod_night lights windows (interior.gdshader, new facade.gdshader for FacadeWindows/FacadeGlass) and darkens the sea.
- Glowing map materials (Tod.EMIT: shop rooms, shop signs, hero signs, neon, ads, lamp lenses) and car head/tail lamp materials
  (Tod.light_car: player, rivals, traffic) follow the time of day. Street lamps: scripts/lamps.gd + shaders/lamp.gdshader
  (glow + ground pool for the 364 world.json lamps, 2 draws). Player headlights: SpotLight3D at night only.
- Test hook: TOURPFX=name sets the tour picture names.
