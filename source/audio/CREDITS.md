# Game sounds: sources (all CC0, real recordings, no synthesis)

- Engine idle, on-throttle blip, start-up: "Car Starting and Accelerating" by jackthemurray, https://freesound.org/people/jackthemurray/sounds/433584/ (CC0)
- Tyre squeal loop: "Tire squeal" #0500, BigSoundBank (Joseph Sardin), https://bigsoundbank.com (CC0)
- Horn: "Horn 3" #3506, BigSoundBank (CC0)

make.py cuts the start-up and horn. psola.py builds eight steady engine loops (900-8400 rpm) from the real engine's own firing
pulses, re-spaced to each rpm (TD-PSOLA), so the recorded engine's tone is kept at every speed. skid.py chains the
squeals that sound alike into one loop. Only real recordings go in; nothing is synthesised from scratch.
