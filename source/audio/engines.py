"""Per-car engine loops from real performance-car recordings (muted.io "Performance Cars" pack, CC0).
Each car gets its own recordings: an idle loop, and loops at higher rpm built only from the firings of a real full-throttle
pull recorded at (or near) that rpm - pitch-synchronous grains of the real engine, re-spaced by a few percent at most where
the recording covers the rpm. Then a per-car tone (EQ) so the two cars never sound alike. Nothing is synthesised.
usage: python3 engines.py <pack dir> <out dir>"""
import sys, glob, numpy as np, soundfile as sf, scipy.signal as ss
SR = 44100; PACK, OUT = sys.argv[1:3]
def load(i):
    f = glob.glob('%s/%s-*.wav' % (PACK, i))[0]; x, s = sf.read(f, always_2d=True); x = ss.resample_poly(x.mean(1), SR, s)
    return ss.filtfilt(*ss.butter(2, 25 / (SR / 2), 'high'), x)

def marks(x, t0, t1, fmin, fmax):
    """one mark per firing: peaks of the low-passed waveform, period followed firing by firing through the pull"""
    y = ss.filtfilt(*ss.butter(4, fmax * 2.0 / (SR / 2)), x); a, b = int(t0 * SR), int(t1 * SR); seg = y[a:b]
    w = seg[:int(0.15 * SR)]; ac = np.correlate(w, w, 'full')[len(w) - 1:]; lo, hi = int(SR / fmax), int(SR / fmin); P = lo + int(np.argmax(ac[lo:hi]))
    m = [a + int(np.argmax(seg[:P]))]
    while m[-1] + int(1.6 * P) < b:
        c = m[-1] + P; r = int(0.22 * P); k = c - r + int(np.argmax(y[c - r:c + r])); P = int(0.75 * P + 0.25 * (k - m[-1]))
        P = int(np.clip(P, SR / (fmax * 1.15), SR / (fmin * 0.87))); m.append(k)
    return np.array(m)

def psola(x, mk, per, nxt, f_out, dur, seed):
    """two-period Hann grains taken along runs of consecutive source firings (so the firing-to-firing character survives),
    laid at the target spacing. mk: grain centres, per: each firing's own period, nxt: index of the next firing in the pool or -1"""
    rng = np.random.default_rng(seed); P_out = SR / f_out; n = int(dur * SR); out = np.zeros(n + SR // 2); t = 0.0; j = -1
    while t < n:
        if j < 0 or nxt[j] < 0 or rng.random() < 1 / 40.0: j = int(rng.integers(0, len(mk)))
        else: j = nxt[j]
        P = int(per[j]); L = min(P, int(P_out)) if P_out < P else P
        if mk[j] - L < 0 or mk[j] + L > len(x): j = -1; continue
        g = x[mk[j] - L:mk[j] + L] * np.hanning(2 * L); g = g / (np.sqrt((g ** 2).mean()) + 1e-9) * (0.8 + 0.2 * rng.random())
        s0 = int(t) - L
        if s0 >= 0: out[s0:s0 + 2 * L] += g
        t += P_out * (1 + rng.normal(0, 0.003))
    return out[:n]

def loop(y, xf=0.25):
    n = int(xf * SR); t = np.linspace(0, np.pi / 2, n); z = y[:-n].copy(); z[:n] = y[:n] * np.sin(t) + y[-n:] * np.cos(t); return z
def flatten(x, win=0.3):
    e = np.sqrt(ss.filtfilt(*ss.butter(2, 1 / win / (SR / 2)), x ** 2).clip(1e-12)); return x * (np.median(e) / e) ** 0.85
def peq(x, f0, gain_db, q):        # one peaking EQ band (RBJ)
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f0 / SR; al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]; a = [1 + al / A, -2 * np.cos(w), 1 - al / A]; return ss.lfilter(b, a, x)

# hz: firing rate per rpm for this car, set from its idle recording so idle -> redline rises evenly; sources are the pull
# (on throttle), the overrun (lift-off, same car) and the idle; each layer takes the source recorded nearest its rpm
CARS = {
    # Vortex: light, high-revving mid-engine car - a fast, raspy full-throttle pull and its lift-off (011), a long even idle (039)
    'vortex': dict(idle=('039', 10.0, 24.0), hz=0.016,
                   src=[('pull', '011', 0.36, 1.66, 70, 160, 0.0), ('over', '011', 1.80, 4.55, 45, 160, 0.06), ('idle', '039', 10.0, 24.0, 25, 42, 0.08)],
                   rpms=[1000, 2000, 3000, 4000, 5000, 6000, 7000, 8100],
                   tone=[(90, -2.0, 0.7), (180, 2.0, 1.0), (2600, 4.0, 0.9), (5200, 2.5, 1.2)], hp=70, lp=11000),
    # Calder: big front-engine V8 GT - a deep, rumbling idle (018) and a long, heavy pull (010)
    'calder': dict(idle=('018', 0.6, 8.2), hz=0.031,
                   src=[('pull', '010', 0.40, 3.32, 55, 220, 0.0), ('idle', '018', 0.6, 8.2, 33, 60, 0.05)],
                   rpms=[800, 1600, 2400, 3200, 4000, 4900, 5900, 7000],
                   tone=[(70, 4.5, 0.8), (140, 2.5, 1.0), (1800, -2.0, 0.8), (4500, -4.0, 0.8)], hp=35, lp=6500),
}

def finish(y, C):
    y = flatten(y, 0.12)                                                            # no puffing from grain to grain
    y = ss.filtfilt(*ss.butter(2, C['hp'] / (SR / 2), 'high'), y); y = ss.filtfilt(*ss.butter(2, C['lp'] / (SR / 2)), y)
    for band in C['tone']: y = peq(y, *band)
    y = y / np.sqrt((y ** 2).mean()) * 0.11; return np.tanh(y * 1.6) / 1.6
def spread(y):                                                                      # how unsteady a loop is: level swing in dB (0.1 s steps)
    e = np.sqrt(np.convolve(y ** 2, np.ones(4410) / 4410, 'valid')[::2205] + 1e-12); l = 20 * np.log10(e); return np.percentile(l, 95) - np.percentile(l, 5)
def build(x, mk, fm, f, seed):
    d = np.abs(np.log(fm / f)); near = np.flatnonzero(d < np.log(1.1))
    if len(near) < 60: near = np.argsort(d)[:60]
    near = np.sort(near); per = (SR / fm[near]).astype(int); pos = {k: q for q, k in enumerate(near)}
    nxt = np.array([pos.get(k + 1, -1) for k in near])
    return loop(psola(x, mk[near], per, nxt, f, 5.0, seed), 0.3), np.median(d[near]), fm[near]

for car, C in CARS.items():
    pools = []
    for kind, fid, t0, t1, fmin, fmax, pen in C['src']:
        x = load(fid); mk = marks(x, t0, t1, fmin, fmax); fl = SR / np.diff(mk); fm = np.r_[fl[0], (fl[:-1] + fl[1:]) / 2, fl[-1]]
        pools.append((kind, x, mk, fm, pen)); print(car, kind, fid, 'firings', len(mk), '%.0f-%.0f Hz' % (np.percentile(fm, 5), np.percentile(fm, 95)))
    # idle: the steadiest 6.5 s of the idle recording, as recorded
    ix = load(C['idle'][0]); idle = flatten(ix[int(C['idle'][1] * SR):int(C['idle'][2] * SR)], 0.5); W = int(6.5 * SR)
    starts = range(0, len(idle) - W, SR // 4); best0 = min(starts, key=lambda a: spread(idle[a:a + W]))
    for n, r in enumerate(C['rpms']):
        if n == 0: y = finish(loop(idle[best0:best0 + W], 0.4), C); print('   %d rpm: idle recording %.1f-%.1f s' % (r, C['idle'][1] + best0 / SR, C['idle'][1] + (best0 + W) / SR))
        else:
            f = r * C['hz']; cands = []
            for kind, x, mk, fm, pen in pools:
                if kind == 'over' and len([q for q in pools if q[0] != 'over']) > 0 and False: continue
                yy, dd, fs = build(x, mk, fm, f, n * 7 + len(car)); yy = finish(yy, C)
                cands.append((dd + pen + 0.03 * spread(yy), kind, yy, fs))
            cost, kind, y, fs = min(cands, key=lambda c: c[0])
            print('   %d rpm: %s, firings %.0f-%.0f Hz -> %.0f Hz (x%.2f), level swing %.1f dB' % (r, kind, fs.min(), fs.max(), f, f / np.median(fs), spread(y)))
        sf.write('%s/eng_%s_%d.wav' % (OUT, car, n), y.astype(np.float32), SR)
        ov = [q for q in pools if q[0] == 'over']
        if ov and n >= 2:                         # off throttle: the same car's real overrun at this rpm
            kind, x, mk, fm, pen = ov[0]; z, dd, fs = build(x, mk, fm, r * C['hz'], n * 11); z = finish(z, C)
            sf.write('%s/eng_%s_off_%d.wav' % (OUT, car, n), z.astype(np.float32), SR)
            print('      off-throttle: overrun %.0f-%.0f Hz (x%.2f), level swing %.1f dB' % (fs.min(), fs.max(), r * C['hz'] / np.median(fs), spread(z)))
