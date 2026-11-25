# Game sounds: sources (all CC0, real recordings, no synthesis)

## Player and rival cars (engines.py)
From the muted.io "Performance Cars" free sample pack (CC0, 68 field recordings, https://muted.io/performance-cars).
The pack's files are only numbered; these are the ones used:
- **Vortex:** 011 (a fast full-throttle pull, then the lift-off overrun of the same car) and 039 (a long, even idle).
- **Calder GT:** 010 (a long, heavy full-throttle pull) and 018 (a deep, rumbling idle).

engines.py follows the engine firing by firing through each pull and builds eight steady loops per car. Every loop takes
only firings that were recorded at (or near) its rpm, so each rpm keeps the real engine's tone there. The idle loop is
the steadiest 6.5 s of the idle recording. Each car then gets its own EQ: the Vortex sharper and raspier, the Calder
deeper and rounder. The Vortex also has off-throttle loops from its real overrun.

## Traffic engines (sfx.py)
- Hatch: "car_idle_loop" by andrewalexander, https://freesound.org/s/369053/ (CC0)
- Saloon: the earlier loop made from "Car Starting and Accelerating" by jackthemurray, https://freesound.org/people/jackthemurray/sounds/433584/ (CC0)
- SUV, van, pickup: muted.io Performance Cars 029, 002 and 016 (steady engine sections; a whistle in 016 notched out)

## Effects (sfx.py, make.py)
- Start-up (starter and catch): jackthemurray 433584 (CC0)
- Crashes: "SSE Vintage Destruction 1" pack by craigsmith, https://freesound.org/people/craigsmith/packs/37728/ (CC0):
  s37-08 hits trash can (light), s37-21 metal gate (medium), s37-34 big auto crash with glass and s38-24 big heavy car crash (heavy)
- Wind and road noise: "Car interior 80 km/h" #0505, BigSoundBank (CC0)
- Tyre squeal: "Tire squeal" #0500 and "Screeching tires 4" #2371, BigSoundBank (CC0)
- Horn: "Horn 3" #3506, BigSoundBank (CC0)

Only real recordings go in: the scripts trim, loop, crossfade, re-space firings by a few percent, filter and set levels.

## Ambience (ambience.py) — CC0 / public domain field recordings
Taken from the loops of two open collections (each credits the original recordings):
- funcoder/omarchy-ambient (Freesound, CC0): sea waves "Crashing Waves - Pacific Ocean" by SecureSubset (https://freesound.org/s/817075/),
  forest birds "Forest quiet atmosphere with some birds" by felix.blume (https://freesound.org/s/414098/), wind "Wind on bushes ...
  close to desert ground" by felix.blume (https://freesound.org/s/711106/), crickets "Crickets (close recording)" by felix.blume
  (https://freesound.org/s/476672/), stream "Relaxing River Sound" by IceVFX (https://freesound.org/s/722875/)
- RinvalAi/brown-noise-library (Wikimedia Commons, CC0): wind in the trees "245286 dbspin grunewald.wav" by dbspin
ambience.py cuts a steady 60-80 s stretch of each (the window with the fewest loud events), crossfades the end into the start
and levels them all to the same loudness.
