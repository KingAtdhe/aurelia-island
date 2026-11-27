# Evens out the tone of each car's engine loops across rpm. The loops are cut from different parts of the recordings
# (idle, pull, overrun), and their long-term spectra jumped from one rpm band to the next (Vortex: share of energy under
# 200 Hz 26/34/19/81/92/73/31/60 %; Calder's top loop 3 % against 97 % below it), so crossfading through the rev range
# swapped the engine's character every 1000 rpm. For each car and each layer (on throttle, overrun) this measures the
# 1/3-octave band levels of every loop, fits a smooth curve per band across the rpm steps (quadratic, least squares),
# and filters each loop towards it (correction limited to +-10 dB, smoothed over neighbouring bands). The filter is
# applied in the frequency domain over the whole loop (circular), so the loop seam stays seamless. Loudness (RMS) is
# then set to what the loop had. Edits godot/assets/audio in place. usage: python3 even_engines.py [--dry]
import subprocess, sys, os, numpy as np
D = os.path.abspath(os.path.dirname(__file__) + '/../../godot/assets/audio'); SR = 44100
def load(f): return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32).astype(np.float64)
def save(f, y): subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "libvorbis", "-q:a", "6", f], input=y.astype(np.float32).tobytes(), check=True)
EDGES = 25.0 * 2 ** (np.arange(0, 30) / 3.0); EDGES = EDGES[EDGES < 16000]          # 1/3-octave bands from 25 Hz
def bands(x):
    S = np.abs(np.fft.rfft(x)) ** 2; fr = np.fft.rfftfreq(len(x), 1 / SR)
    b = np.array([S[(fr >= lo) & (fr < hi)].mean() + 1e-12 for lo, hi in zip(EDGES[:-1], EDGES[1:])])
    return 10 * np.log10(b / b.sum())
def low_share(x):
    S = np.abs(np.fft.rfft(x)) ** 2; fr = np.fft.rfftfreq(len(x), 1 / SR); return S[fr < 200].sum() / S.sum()
dry = '--dry' in sys.argv
for car, layers in {"vortex": {"on": list(range(8)), "off": list(range(2, 8))}, "calder": {"on": list(range(8))}}.items():
    for layer, ks in layers.items():
        names = ["eng_%s_%s%d" % (car, "off_" if layer == "off" else "", k) for k in ks]
        X = [load("%s/%s.ogg" % (D, n)) for n in names]; B = np.array([bands(x) for x in X])
        t = np.arange(len(ks), dtype=float); T = np.zeros_like(B)
        for j in range(B.shape[1]): T[:, j] = np.polyval(np.polyfit(t, B[:, j], 2 if len(ks) > 3 else 1), t)
        C = np.clip(T - B, -10, 10); C = np.array([np.convolve(np.pad(c, 1, mode="edge"), [0.25, 0.5, 0.25], "valid") for c in C])
        mid = np.sqrt(EDGES[:-1] * EDGES[1:])
        for n, x, c in zip(names, X, C):
            fr = np.fft.rfftfreq(len(x), 1 / SR); g_db = np.interp(np.log(np.maximum(fr, 1)), np.log(mid), c)
            y = np.fft.irfft(np.fft.rfft(x) * 10 ** (g_db / 20), len(x)); y *= np.sqrt((x ** 2).mean() / (y ** 2).mean())
            if np.abs(y).max() > 0.98: y *= 0.98 / np.abs(y).max()
            print("%-18s low<200Hz %3.0f%% -> %3.0f%%   max boost %+.1f cut %+.1f dB" % (n, 100 * low_share(x), 100 * low_share(y), c.max(), c.min()))
            if not dry: save("%s/%s.ogg" % (D, n), y)
