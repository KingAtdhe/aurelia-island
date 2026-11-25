# Rain and storm sound for the Godot game: real CC0 / public-domain recordings only (CREDITS.md, "Weather").
# Beds: the two collections' rain loops (already seamless) levelled and re-encoded. Thunder: four rolls cut from the
# omarchy-ambient storm recording (Sheyvan, "Rain and Thunder Ambience Tuebingen"), faded in and out.
# usage: python3 weather.py <omarchy-ambient/sounds> <brown-noise-library/sounds> <out>
import sys, subprocess, numpy as np, os
A, B, OUT = sys.argv[1:4]; SR = 48000
def load(f, t0=0.0, n=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(t0)] + (["-t", str(n)] if n else []) + ["-i", f, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)
def save(x, name):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "libvorbis", "-q:a", "3", "%s/%s.ogg" % (OUT, name)], input=np.clip(x, -0.99, 0.99).astype(np.float32).tobytes(), check=True)
    print(name, round(len(x) / SR, 1), "s", os.path.getsize("%s/%s.ogg" % (OUT, name)) // 1024, "KB")
def level(x, db): return x * 10 ** (db / 20) / np.sqrt((x ** 2).mean())
save(level(load(B + "/light-rain-woods.ogg"), -20.0), "wx_rain")
save(level(load(B + "/summer-thunderstorm.ogg"), -19.0), "wx_storm")
for k, (t0, n) in enumerate([(89.0, 12.0), (188.0, 12.0), (233.0, 18.0), (273.0, 19.0)]):
    x = load(A + "/storm.ogg", t0, n); f = int(0.15 * SR); g = int(2.5 * SR)
    x[:f] *= np.linspace(0, 1, f)[:, None]; x[-g:] *= np.linspace(1, 0, g)[:, None] ** 2
    x *= 0.5 / np.abs(x).max()
    save(x, "wx_thunder_%d" % k)
