# Ambient loops for the Godot game: real CC0 / public-domain field recordings only (see CREDITS.md, "Ambience").
# Each loop: a steady stretch of the recording, end crossfaded into the start (3 s, equal power), levelled to the same
# loudness, 48 kHz stereo Ogg Vorbis. usage: python3 ambience.py <omarchy-ambient/sounds> <brown-noise-library/sounds> <out>
import sys, subprocess, numpy as np, os
A, B, OUT = sys.argv[1:4]; SR = 48000; XF = 3.0
SRC = {          # name: (file, start s, length s, level dB RMS)
    "amb_waves": (A + "/waves.ogg", 190.0, 80.0, -20.0),
    "amb_birds": (A + "/birds.ogg", 60.0, 80.0, -22.0),
    "amb_wind": (A + "/wind.ogg", 116.0, 80.0, -21.0),
    "amb_trees": (B + "/wind-in-trees.ogg", 10.0, 80.0, -21.0),
    "amb_crickets": (A + "/crickets.ogg", 126.0, 80.0, -22.0),
    "amb_stream": (A + "/stream.ogg", 30.0, 60.0, -21.0),
}
def load(f, t0, n):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(n), "-i", f, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
for name, (f, t0, n, db) in SRC.items():
    x = load(f, t0, n + XF); k = int(XF * SR); body = x[:-k].copy(); tail = x[-k:]
    t = np.linspace(0, np.pi / 2, k)[:, None]
    body[:k] = body[:k] * np.sin(t) + tail * np.cos(t)          # the end flows into the start
    rms = np.sqrt((body ** 2).mean()); body *= 10 ** (db / 20) / rms
    body = np.clip(body, -0.99, 0.99)
    p = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "libvorbis", "-q:a", "3", "%s/%s.ogg" % (OUT, name)], input=body.astype(np.float32).tobytes(), check=True)
    print(name, round(len(body) / SR, 1), "s", os.path.getsize("%s/%s.ogg" % (OUT, name)) // 1024, "KB")
