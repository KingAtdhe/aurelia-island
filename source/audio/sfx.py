"""Crashes, wind/road noise and the traffic cars' engines, cut from Saba's CC0 uploads (trims, fades, loops, EQ, level only).
usage: python3 sfx.py <uploads dir> <muted pack dir> <crash pack dir> <out dir>"""
import sys, glob, numpy as np, soundfile as sf, scipy.signal as ss
SR = 44100; UP, PACK, CR, OUT = sys.argv[1:5]
def load(f):
    x, s = sf.read(f, always_2d=True); x = x.mean(1); x = ss.resample_poly(x, SR, s) if s != SR else x
    return ss.filtfilt(*ss.butter(2, 25 / (SR / 2), 'high'), x)
def one(pat, d): return glob.glob('%s/*%s*' % (d, pat))[0]
def seg(x, a, b): return x[int(a * SR):int(b * SR)].copy()
def fade(x, i=0.004, o=0.4):
    x = x.copy(); n = int(i * SR); x[:n] *= np.linspace(0, 1, n); n = int(o * SR); x[-n:] *= np.linspace(1, 0, n) ** 2; return x
def loop(y, xf=0.3):
    n = int(xf * SR); t = np.linspace(0, np.pi / 2, n); z = y[:-n].copy(); z[:n] = y[:n] * np.sin(t) + y[-n:] * np.cos(t); return z
def flatten(x, win=0.4):
    e = np.sqrt(ss.filtfilt(*ss.butter(2, 1 / win / (SR / 2)), x ** 2).clip(1e-12)); return x * (np.median(e) / e) ** 0.85
def lp(x, f): return ss.filtfilt(*ss.butter(2, f / (SR / 2)), x)
def hp(x, f): return ss.filtfilt(*ss.butter(2, f / (SR / 2), 'high'), x)
def save(name, x, peak=0.9):
    x = x * (peak / (np.abs(x).max() + 1e-9)); sf.write('%s/%s.wav' % (OUT, name), x.astype(np.float32), SR); print(name, '%.2fs' % (len(x) / SR))
def rms(x, r=0.12): return x * (r / np.sqrt((x ** 2).mean()))

# crashes: the impact and its debris, from the first hit
save('crash_light', fade(seg(load(one('s37-08', CR)), 0.03, 1.25), o=0.5), 0.75)
save('crash_mid', fade(seg(load(one('s37-21', CR)), 0.03, 1.7), o=0.6), 0.85)
save('crash_heavy_a', fade(seg(load(one('s37-34', CR)), 0.0, 2.5), o=0.9), 0.95)
save('crash_heavy_b', fade(seg(load(one('s38-24', CR)), 0.05, 2.2), o=0.8), 0.95)
# wind and road: the car interior at 80 km/h, steady loop; the game raises level and pitch with speed
w = load(one('Car_interior_80km', UP)); n = len(w) / SR
save('wind_road', rms(loop(flatten(seg(w, 1.0, min(n - 0.5, 9.0))), 0.5)), 0.8)
# traffic: a different real engine for every model, softened for distance
t = { 'traffic_hatch': (load(one('369053__andrewalexander', UP)), 0.2, 6.5, 5000),
      'traffic_suv': (load(one('029-', PACK)), 6.0, 13.0, 4000),
      'traffic_van': (load(one('002-', PACK)), 2.0, 9.5, 3500),
      'traffic_pickup': (load(one('016-', PACK)), 3.9, 7.8, 3800) }
def dewhine(x, lo=2500, hi=3700):                          # a steady whistle from something else in the recording: notch it out
    f, P = ss.welch(x, SR, nperseg=16384); b = (f > lo) & (f < hi); f0 = f[b][np.argmax(P[b])]
    for k in (1, 2): x = ss.filtfilt(*ss.iirnotch(f0 * k, 6.0, SR), x)
    return x
for k, (x, a, b, cut) in t.items():
    y = seg(x, a, b)
    if k == 'traffic_pickup': y = dewhine(y)
    save(k, rms(lp(loop(flatten(y), 0.4), cut)), 0.8)
# start-up: the starter and the catch only (the car's own idle loop takes over in the game)
j = load(one('433584__jackthemurray', UP)); save('eng_crank', fade(seg(j, 1.1, 2.25), o=0.35), 0.85)
