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
