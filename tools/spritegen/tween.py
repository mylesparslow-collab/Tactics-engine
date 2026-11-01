"""In-betweening: insert interpolated poses between key poses so motion stops popping.

Works on any unit whose frames are pose dicts (kit humanoids, creatures, hand-built units):
numbers and numpy arrays are interpolated with easing, direction vectors (item_*, blade) are
re-normalised, and anything else (None, strings) snaps to the nearer key. Look overrides
(hit flash) stay on their key frame only.

Each row keeps its duration: frame count goes up, fps goes up by the same factor.
"""
import numpy as np

DIR_KEYS = ('item_r', 'item_l', 'blade')


def ease(t):
    return t * t * (3 - 2 * t)          # smoothstep: slow out of a key, slow into the next


def lerp_pose(a, b, t):
    out = {}
    for k, va in a.items():
        vb = b.get(k, va)
        if va is None or vb is None or isinstance(va, (str, bool)) or isinstance(vb, (str, bool)):
            out[k] = va if t < 0.5 else vb
            continue
        try:
            v = np.asarray(va, dtype=np.float64) * (1 - t) + np.asarray(vb, dtype=np.float64) * t
        except (TypeError, ValueError):
            out[k] = va if t < 0.5 else vb
            continue
        if k in DIR_KEYS and np.ndim(v) == 1:
            n = np.linalg.norm(v)
            v = v / n if n > 1e-6 else np.asarray(vb, dtype=np.float64)
        out[k] = v if np.ndim(v) else float(v)
    return out


def tween_row(keys, loop, steps=1, eased=True):
    """keys: [(pose, look_overrides)]. Insert `steps` poses between consecutive keys."""
    n = len(keys)
    if n < 2:
        return list(keys), list(range(n))
    out, key_index = [], []
    pairs = n if loop else n - 1
    for i in range(pairs):
        a, la = keys[i]
        b, _ = keys[(i + 1) % n]
        key_index.append(len(out))
        out.append((a, la))
        for s in range(1, steps + 1):
            t = s / (steps + 1)
            out.append((lerp_pose(a, b, ease(t) if eased else t), {}))
    if not loop:
        key_index.append(len(out))
        out.append(keys[-1])
    return out, key_index


def tween_all(frames, rows, steps=None):
    """frames: {row: [(pose, look)]}; rows: [(name, fps, loop, extra)]. Returns (frames, rows)."""
    steps = steps or {'idle': 1, 'move': 1, 'attack': 1, 'hit': 1, 'death': 1, 'cast': 1}
    new_frames, new_rows = {}, []
    for name, fps, loop, extra in rows:
        keys = frames[name]
        st = steps.get(name, 1)
        seq, kidx = tween_row(keys, loop, st)
        new_frames[name] = seq
        factor = len(seq) / max(len(keys), 1)
        ex = dict(extra)
        if 'hitFrame' in ex:
            ex['hitFrame'] = kidx[min(ex['hitFrame'], len(kidx) - 1)]
        new_rows.append((name, max(1, int(round(fps * factor))), loop, ex))
    return new_frames, new_rows
