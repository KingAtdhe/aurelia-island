"""Cut a triangle mesh along the zero isoline of a per-vertex scalar, so zone borders are exact curves, not jagged face edges."""
import numpy as np

def cut(V, F, g, eps=1e-7):
    g = np.where(np.abs(g) < eps, eps, g)
    neg = g[F] < 0; cnt = neg.sum(1)
    keep = F[(cnt == 0) | (cnt == 3)]; X = F[(cnt == 1) | (cnt == 2)]; nx = neg[(cnt == 1) | (cnt == 2)]
    if not len(X): return V, F
    # lone vertex: the one whose sign differs from the other two
    lone = np.where(nx.sum(1) == 1, np.argmax(nx, 1), np.argmin(nx, 1))
    a = X[np.arange(len(X)), lone]; b = X[np.arange(len(X)), (lone + 1) % 3]; c = X[np.arange(len(X)), (lone + 2) % 3]
    E = np.r_[np.c_[a, b], np.c_[a, c]]; Es = np.sort(E, 1)
    uniq, inv = np.unique(Es, axis=0, return_inverse=True); inv = inv.ravel()
    t = g[uniq[:, 0]] / (g[uniq[:, 0]] - g[uniq[:, 1]])
    P = V[uniq[:, 0]] + (V[uniq[:, 1]] - V[uniq[:, 0]]) * t[:, None]
    base = len(V); V2 = np.r_[V, P]; pab = base + inv[:len(X)]; pac = base + inv[len(X):]
    T = np.r_[np.c_[a, pab, pac], np.c_[pab, b, c], np.c_[pab, c, pac]]
    return V2, np.r_[keep, T]

def weld(V, F, tol=1e-6):
    q = np.round(V / tol).astype(np.int64); _, idx, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    F2 = inv.ravel()[F]; ok = (F2[:, 0] != F2[:, 1]) & (F2[:, 1] != F2[:, 2]) & (F2[:, 0] != F2[:, 2])
    return V[idx], F2[ok]
