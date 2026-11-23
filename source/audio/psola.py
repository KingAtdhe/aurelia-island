"""Engine loops at fixed rpm from the real recording: pitch-synchronous grains of the real engine re-spaced to the target firing rate
(TD-PSOLA). The timbre stays the recorded car's; only the firing rate changes. Higher loops take their grains from the throttle blips."""
import numpy as np, soundfile as sf, scipy.signal as ss, sys
sys.path.insert(0, '/home/claude/snd'); SR = 44100
def load(f):
    x, sr = sf.read(f); x = x.mean(1) if x.ndim > 1 else x
    x = ss.resample_poly(x, SR, sr) if sr != SR else x
    return ss.filtfilt(*ss.butter(2, 25 / (SR / 2), 'high'), x)
def marks(x, t0, t1, fmin, fmax):
    """pitch marks: one per firing, at the peak of the low-passed waveform, tracked period by period"""
    y = ss.filtfilt(*ss.butter(4, fmax * 1.5 / (SR / 2)), x); a, b = int(t0 * SR), int(t1 * SR); seg = y[a:b]
    # starting period from autocorrelation
    w = seg[:int(0.3 * SR)]; ac = np.correlate(w, w, 'full')[len(w) - 1:]; lo, hi = int(SR / fmax), int(SR / fmin); P = lo + np.argmax(ac[lo:hi])
    m = [a + int(np.argmax(seg[:P]))]
    while m[-1] + int(1.5 * P) < b:
        c = m[-1] + P; r = int(0.25 * P); k = c - r + int(np.argmax(y[c - r:c + r])); P = int(0.7 * P + 0.3 * (k - m[-1])); m.append(k)
    return np.array(m)
def psola(x, mk, f_out, dur):
    """overlap-add two-period Hann grains taken from the source marks at the target spacing"""
    P_out = SR / f_out; n = int(dur * SR); j = 1; out = np.zeros(n + 4 * SR // 10); t = 0.0; i = 0; rng = np.random.default_rng(3)
    while t < n:
        if i == 0 or j >= len(mk) - 2 or (mk[j + 1] - mk[j]) > 2 * (mk[j] - mk[j - 1]) or rng.random() < 0.01: j = int(rng.integers(1, len(mk) - 40))   # wander through the takes, never a fixed cycle
        else: j += 1
        P = (mk[j + 1] - mk[j - 1]) // 2
        L = min(P, int(P_out * 1.0)) if P_out < P else P                                     # shrink grains a little for big pitch-ups (less buzz)
        g = x[mk[j] - L:mk[j] + L] * np.hanning(2 * L); g = g / (np.sqrt((g ** 2).mean()) + 1e-9) * (0.7 + 0.3 * rng.random() ** 2) ; s0 = int(t) - L   # even grain level: no puffing
        if s0 >= 0: out[s0:s0 + 2 * L] += g
        t += P_out * (1 + rng.normal(0, 0.004)); i += 1                                      # a touch of real-engine jitter
    return out[:n]
def loop(x, xf=0.15):
    n = int(xf * SR); tt = np.linspace(0, np.pi / 2, n); y = x[:-n].copy(); y[:n] = x[:n] * np.sin(tt) + x[-n:] * np.cos(tt); return y
j = load('/home/claude/snd/in/d58ff781-433584__jackthemurray__car-starting-and-accelerating.wav')
mi = marks(j, 4.0, 9.9, 35, 70)            # idle grains (47.5 Hz)
mb = np.r_[marks(j, 13.95, 14.95, 70, 130), marks(j, 15.7, 16.2, 70, 130), marks(j, 16.55, 17.25, 70, 130)]     # on-throttle grains (~95 Hz)
print('marks idle', len(mi), 'blip', len(mb))
# a four-cylinder fires twice per revolution: f = rpm / 30
RPMS = [900, 1400, 2100, 3000, 4100, 5400, 6900, 8400]
for r in RPMS:
    f = r / 30.0; src = mi if r < 2500 else mb
    y = psola(j, src, f, 4.3); y = ss.filtfilt(*ss.butter(2, 60 / (SR / 2), "high"), y); y = loop(y, 0.3)
    y = y / np.sqrt((y ** 2).mean()) * 0.12; y = np.clip(y, -0.95, 0.95)
    sf.write('/home/claude/snd/out/eng_%d.wav' % r, y.astype(np.float32), SR); print(r, 'rpm', round(f, 1), 'Hz', round(len(y) / SR, 2), 's')
