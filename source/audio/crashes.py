# Crash sounds for the Godot game, cut from real recordings (craigsmith "SSE Vintage Destruction" packs, CC0; see CREDITS.md).
# Each cut starts 25 ms before the impact (found as the sharpest jump in loudness near the marked time, read off the
# spectrograms: the broadband hit after the tyre squeal), keeps the crunch and debris that follow, and fades out.
# usage: python3 crashes.py <dir with the craigsmith wav files> <out>
import sys, subprocess, numpy as np, os, glob
SRC, OUT = sys.argv[1:3]; SR = 44100
CUTS = {          # name: (file id, marked impact s, length s)
    "crash_car_a": ("675903", -10.74, 2.2),      # cadillac rear-ends a car (negative: fixed start, after the squeal)
    "crash_car_b": ("675905", 13.27, 2.4),       # crash in skids, metal debris
    "crash_rail_a": ("675907", 6.90, 1.8),       # dirt skid hits a metal rail, glass
    "crash_rail_b": ("675912", 11.20, 2.0),      # round a corner, hits metal
    "crash_hard": ("675915", 13.22, 2.2),        # long skid, crash
}
def load(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
for name, (fid, t, n) in CUTS.items():
    f = glob.glob("%s/%s__*.wav" % (SRC, fid))[0]; x = load(f)
    h = int(0.005 * SR); e = np.sqrt(np.convolve(x ** 2, np.ones(h) / h, "same"))
    a, b = int((abs(t) - 0.3) * SR), int((abs(t) + 0.3) * SR)
    prev = np.array([e[max(0, i - int(0.06 * SR)):i - h].mean() + 1e-4 for i in range(a, b, h)])
    cur = e[a:b:h][:len(prev)]; k = a + int(np.argmax(cur / prev)) * h           # the sharpest jump: the moment of impact
    if t < 0: k = int(-t * SR) + int(0.025 * SR)
    s = max(0, k - int(0.025 * SR)); y = x[s:s + int(n * SR)].copy()
    f_in = int(0.004 * SR); y[:f_in] *= np.linspace(0, 1, f_in)
    f_out = int(0.6 * SR); y[-f_out:] *= np.linspace(1, 0, f_out) ** 2
    y *= 0.95 / np.abs(y).max()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "libvorbis", "-q:a", "5", "%s/%s.ogg" % (OUT, name)], input=y.astype(np.float32).tobytes(), check=True)
    print(name, "impact at %.3f s" % (k / SR), "peak in first 0.3 s: %.2f" % np.abs(y[:int(0.3 * SR)]).max())
