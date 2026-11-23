"""Cut Saba's uploaded CC0 recordings into game loops (no synthesis: only trims, crossfades, gain and filtering of the real recordings)."""
import numpy as np, soundfile as sf, scipy.signal as ss
SR = 44100
def load(f):
    x, sr = sf.read(f); x = x.mean(1) if x.ndim > 1 else x
    if sr != SR: x = ss.resample_poly(x, SR, sr)
    b, a = ss.butter(2, 25 / (SR / 2), 'high'); return ss.filtfilt(b, a, x)        # rumble / DC off
def seg(x, t0, t1): return x[int(t0 * SR):int(t1 * SR)].copy()
def flatten(x, win=0.25):                                                          # even out slow level drift
    e = np.sqrt(ss.filtfilt(*ss.butter(2, 1 / win / (SR / 2)), x ** 2).clip(1e-12)); return x * (np.median(e) / e) ** 0.8
def loop(x, xf=0.12):                                                              # equal-power crossfade of the tail into the head
    n = int(xf * SR); t = np.linspace(0, np.pi / 2, n)
    y = x[:-n].copy(); y[:n] = x[:n] * np.sin(t) + x[-n:] * np.cos(t); return y
def best_loop_len(x, f0, xf=0.12):                                                 # end the loop on a whole number of engine firings
    per = SR / f0; n = len(x); k = int((n - xf * SR) / per); return x[:int(k * per + xf * SR)]
def norm(x, peak=0.89): return x * (peak / np.abs(x).max())
def save(name, x): sf.write('/home/claude/snd/out/%s.wav' % name, x.astype(np.float32), SR); print(name, round(len(x) / SR, 2), 's')

j = load('d58ff781-433584__jackthemurray__car-starting-and-accelerating.wav')
# idle, exhaust side: steady 47.5 Hz stretch 4.0-9.9 s
idle = flatten(seg(j, 4.0, 9.9)); save('eng_idle', norm(loop(best_loop_len(idle, 47.5))))
# on-throttle mid revs (~93 Hz, about three times idle): the steadiest blip
mid = flatten(seg(j, 13.95, 14.95), 0.15); save('eng_mid', norm(loop(best_loop_len(mid, 93.6, 0.1), 0.1)))
mid2 = flatten(seg(j, 16.55, 17.30), 0.15); save('eng_mid2', norm(loop(best_loop_len(mid2, 93.8, 0.1), 0.1)))
# engine start: crank and catch, fading into the idle level
st = seg(j, 1.1, 2.9); fo = np.ones_like(st); n = int(0.5 * SR); fo[-n:] = np.linspace(1, 0, n); save('eng_start', norm(st * fo))
# traffic: the interior idle of the Honda, already loopable
a = load('17d00174-369053__andrewalexander__car_idle_loop.wav'); save('traffic_idle', norm(loop(a, 0.3), 0.7))
# tyre squeal loop: the sustained cores of several real squeals, chained with crossfades
s4 = load('4903b9fc-VEHSkid_Screeching_tires_4_ID_2371_BigSoundBank.com.wav'); s5 = load('squeal500.wav')
e5 = np.sqrt(ss.filtfilt(*ss.butter(2, 8 / (SR / 2)), s5 ** 2).clip(1e-12)); on = e5 > e5.max() * 0.25
edges = np.flatnonzero(np.diff(on.astype(int))); cores = []
for a0, a1 in zip(edges[::2], edges[1::2]):
    if (a1 - a0) / SR > 0.35: cores.append(s5[a0 + int(0.05 * SR):a1 - int(0.05 * SR)])
cores = [c * (0.2 / np.sqrt((c ** 2).mean())) for c in cores[:6]] + [seg(s4, 4.55, 5.95) * (0.2 / np.sqrt((seg(s4, 4.55, 5.95) ** 2).mean()))]
xf = int(0.08 * SR); out = cores[0]
for c in cores[1:]:
    t = np.linspace(0, np.pi / 2, xf); out = np.concatenate([out[:-xf], out[-xf:] * np.cos(t) + c[:xf] * np.sin(t), c[xf:]])
save('skid_loop', norm(loop(out, 0.08), 0.8))
h = load('660bbd43-VEHHorn_Horn_3_ID_3506_BigSoundBank.com.wav'); fo = np.ones_like(h); fo[-int(0.04 * SR):] = np.linspace(1, 0, int(0.04 * SR)); save('horn', norm(h * fo, 0.85))
