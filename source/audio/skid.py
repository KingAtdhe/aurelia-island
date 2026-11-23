"""Tyre squeal loop from the real squeals of BigSoundBank #0500: only takes that sound alike, levelled and chained with long crossfades."""
import numpy as np, soundfile as sf, scipy.signal as ss
SR = 44100
x, sr = sf.read('/home/claude/snd/in/squeal500.wav'); x = ss.resample_poly(x, SR, sr); x = ss.filtfilt(*ss.butter(2, 300 / (SR / 2), 'high'), x)
e = np.sqrt(ss.filtfilt(*ss.butter(2, 8 / (SR / 2)), x ** 2).clip(1e-12)); on = e > e.max() * 0.3
ed = np.flatnonzero(np.diff(on.astype(int))); cores = []
for a, b in zip(ed[::2], ed[1::2]):
    a += int(0.06 * SR); b -= int(0.06 * SR)
    if (b - a) / SR < 0.3: continue
    c = x[a:b]; f, P = ss.welch(c, SR, nperseg=4096); band = (f > 800) & (f < 6000); fp = f[band][np.argmax(P[band])]
    cores.append((fp, c))
fps = np.array([c[0] for c in cores]); med = np.median(fps); print('squeal pitches', np.round(fps).astype(int), 'median', round(med))
keep = [c for fp, c in cores if abs(fp - med) / med < 0.15]; print('kept', len(keep))
def level(c):
    env = np.sqrt(ss.filtfilt(*ss.butter(2, 6 / (SR / 2)), c ** 2).clip(1e-12)); return c / env * 0.2
keep = [level(c) for c in keep]
xf = int(0.15 * SR); out = keep[0]
for c in keep[1:]:
    t = np.linspace(0, np.pi / 2, xf); out = np.concatenate([out[:-xf], out[-xf:] * np.cos(t) + c[:xf] * np.sin(t), c[xf:]])
t = np.linspace(0, np.pi / 2, xf); y = out[:-xf].copy(); y[:xf] = out[:xf] * np.sin(t) + out[-xf:] * np.cos(t)
y = y / np.abs(y).max() * 0.8; sf.write('/home/claude/snd/out/skid_loop.wav', y.astype(np.float32), SR); print('skid loop', round(len(y) / SR, 2), 's')
