# Re-cut the game's crash sounds so the hit is at the start: some cuts began on tyre squeal or a lead-in and reached
# their main impact 0.15-1.3 s later (crash_car_a peaked at 1.3 s), so the sound lagged behind the crash on screen.
# For each file: the first moment the 5 ms loudness comes within 10 dB of its peak is the hit; start 10 ms before it with a 3 ms fade-in; long flat cuts are cut to MAXLEN with a fade-out. Edits godot/assets/audio in place.
# usage: python3 align_crashes.py [--dry]
import subprocess, sys, numpy as np, os
D = os.path.abspath(os.path.dirname(__file__) + '/../../godot/assets/audio'); SR = 44100
MAXLEN = {"crash_car_b": 1.5, "crash_car_a": 1.7}
def load(f):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32).astype(np.float64)
for n in ["crash_light", "crash_mid", "crash_heavy_a", "crash_heavy_b", "crash_car_a", "crash_car_b", "crash_rail_a", "crash_rail_b", "crash_hard"]:
    f = "%s/%s.ogg" % (D, n); x = load(f); h = int(0.005 * SR)
    e = np.sqrt(np.convolve(x ** 2, np.ones(h) / h, "same")) + 1e-5
    first_loud = int(np.argmax(e > 0.3 * e.max()))          # the hit: the first time the sound gets within 10 dB of its loudest
    s = max(0, first_loud - int(0.01 * SR))
    y = x[s:].copy(); L = MAXLEN.get(n)
    if L and len(y) > L * SR: y = y[:int(L * SR)]
    fi = int(0.003 * SR); y[:fi] *= np.linspace(0, 1, fi); fo = int(min(0.5, len(y) / SR * 0.35) * SR); y[-fo:] *= np.linspace(1, 0, fo) ** 2
    y *= 0.95 / np.abs(y).max()
    pk = np.argmax(np.abs(y)) / SR
    print("%-14s cut %.3f s off the start, now %.2f s, loudest at %.0f ms" % (n, s / SR, len(y) / SR, pk * 1000))
    if '--dry' not in sys.argv:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "libvorbis", "-q:a", "5", f], input=y.astype(np.float32).tobytes(), check=True)
