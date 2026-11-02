#!/usr/bin/env python3
"""Arrange the menu and battle music out of REAL recorded instrument samples.

No oscillators: every note is a recording from Meta's CC0 "Meta Piano" (88 keys x 4 velocity layers),
percussion hits are Kenney CC0 impact recordings pitched down, and the drone bed is a recording from the
Oculus Audio Pack (CC BY 4.0). We only choose the notes, time them, pan, and add a room reverb.

Usage: python3 tools/sounds/compose.py <packs-dir>
"""
import os, subprocess, sys
import numpy as np

PACKS = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/packs'
PIANO = f'{PACKS}/Meta-open-sound/systems/instruments/meta-piano/ogg'
OCU = f'{PACKS}/Meta-open-sound/corpora/oculus-audio-pack/ogg'
KX = f'{PACKS}/kenney-impact-sounds-for-godot/addons/kenney impact sounds'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src', 'audio', 'assets', 'music')
SR = 44100
rng = np.random.default_rng(7)
_cache = {}

def load(path, speed=1.0):
    key = (path, speed)
    if key not in _cache:
        af = f'asetrate={int(SR * speed)},aresample={SR}' if speed != 1.0 else 'anull'
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-af', af, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                             capture_output=True, check=True).stdout
        _cache[key] = np.frombuffer(raw, dtype=np.float32).copy()
    return _cache[key]

NAMES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11,
         'Db': 1, 'Eb': 3, 'Gb': 6, 'Ab': 8, 'Bb': 10}
SHARP = ['C', 'Cs', 'D', 'Ds', 'E', 'F', 'Fs', 'G', 'Gs', 'A', 'As', 'B']

def midi(n):
    name, octv = n[:-1], int(n[-1])
    return 12 * (octv + 1) + NAMES[name]

def piano_file(m, vel):
    return f'{PIANO}/INSPiano_Vel0{vel}_{SHARP[m % 12]}{m // 12 - 1}_01.ogg'

class Mix:
    def __init__(self, seconds):
        self.n = int(seconds * SR)
        self.L = np.zeros(self.n, dtype=np.float32)
        self.R = np.zeros(self.n, dtype=np.float32)
        self.dry_L = np.zeros(self.n, dtype=np.float32)

    def put(self, sig, t, gain=1.0, pan=0.0, wet=1.0):
        i = int(max(0, t) * SR)
        if i >= self.n: return
        seg = sig[: self.n - i]
        # equal-power pan, pan in [-1, 1]
        a = (pan + 1) * np.pi / 4
        self.L[i:i + len(seg)] += seg * gain * np.cos(a)
        self.R[i:i + len(seg)] += seg * gain * np.sin(a)

    def note(self, name, t, dur, vel=2, gain=0.5, pan=0.0, human=0.010):
        m = midi(name)
        s = load(piano_file(m, vel)).copy()
        n = int(dur * SR)
        if n < len(s):
            rel = int(0.45 * SR)
            end = min(len(s), n + rel)
            s = s[:end]
            fade = np.ones(len(s), dtype=np.float32)
            fade[n:] = np.linspace(1, 0, end - n) ** 2
            s *= fade
        jitter = rng.normal(0, human) if human else 0
        self.put(s, t + jitter, gain * float(rng.uniform(0.9, 1.05)), pan)

    def hit(self, path, t, gain=0.5, speed=1.0, pan=0.0):
        self.put(load(path, speed), t + rng.normal(0, 0.004), gain * float(rng.uniform(0.9, 1.05)), pan)

    def bed(self, path, gain, speed=1.0):
        s = load(path, speed)
        reps = int(np.ceil(self.n / len(s)))
        tiled = np.tile(s, reps)[: self.n]
        self.L += tiled * gain
        self.R += tiled * gain

def reverb(L, R, seconds=3.2, mix=0.28, damp=0.6):
    """Room reverb: convolve with a decaying, low-passed noise impulse response (processing of the performance)."""
    n = int(seconds * SR)
    out = []
    for ch, x in enumerate((L, R)):
        ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.linspace(0, 6.5, n)).astype(np.float32)
        k = np.ones(int(SR / 4000 * (1 + damp * 4))) / (SR / 4000 * (1 + damp * 4))
        ir = np.convolve(ir, k, mode='same').astype(np.float32)
        ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))   # soft onset
        size = len(x) + n
        nf = 1 << (size - 1).bit_length()
        y = np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(ir, nf), nf)[:size].astype(np.float32)
        y /= np.max(np.abs(y)) + 1e-9
        y *= np.max(np.abs(x)) * 0.9
        out.append(y)
    wet_L, wet_R = out
    return wet_L, wet_R

def fold_loop(L, R, loop_len):
    """Fold everything after loop_len (reverb/ring tails) back onto the start so the loop is seamless."""
    n = int(loop_len * SR)
    def f(x):
        body = x[:n].copy()
        tail = x[n:]
        k = 0
        while k < len(tail):
            seg = tail[k:k + n]
            body[: len(seg)] += seg
            k += n
        return body
    return f(L), f(R)

def finish(mix, loop_len, name, wet=0.3, rv=3.2, target_peak=0.89, bitrate='112k'):
    wL, wR = reverb(mix.L, mix.R, seconds=rv)
    n = len(wL)
    L = np.pad(mix.L, (0, n - len(mix.L))) + wL * wet
    R = np.pad(mix.R, (0, n - len(mix.R))) + wR * wet
    L, R = fold_loop(L, R, loop_len)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)))
    L, R = L / peak * target_peak, R / peak * target_peak
    st = np.stack([L, R], axis=1).astype(np.float32)
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, name + '.mp3')
    # loudnorm to a consistent music level, encode stereo MP3
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-',
                    '-af', 'loudnorm=I=-22:TP=-2:LRA=9', '-codec:a', 'libmp3lame', '-b:a', bitrate, out],
                   input=st.tobytes(), check=True)
    print(name, f'{loop_len:.1f}s', os.path.getsize(out) // 1024, 'KB')

def chord(root, kind):
    iv = {'m': (0, 3, 7), 'M': (0, 4, 7), 'm7': (0, 3, 7, 10), 'M7': (0, 4, 7, 11), 'sus2': (0, 2, 7), 'dom': (0, 4, 7, 10)}[kind]
    return [root + i for i in iv]

def nm(m):
    return SHARP[m % 12].replace('s', '#') + str(m // 12 - 1)

# ------------------------------------------------------------------------------------------------------------
# MENU: "Low Water" - slow, spacious piano over a drone. D aeolian.
def menu():
    bpm, bars = 54, 16
    beat = 60 / bpm
    bar = 4 * beat
    loop_len = bars * bar
    mx = Mix(loop_len + 14)
    # chord per bar (root midi, kind)
    D3, Bb2, F3, C3, G2, A2 = 50, 46, 53, 48, 43, 45
    prog = [(D3, 'm'), (Bb2, 'M'), (F3, 'M'), (C3, 'M'), (D3, 'm'), (Bb2, 'M'), (G2, 'm'), (A2, 'dom')] * 2
    for b, (root, kind) in enumerate(prog):
        t0 = b * bar
        tones = chord(root, kind)
        # bass: root low, held; fifth halfway
        mx.note(nm(root - 12), t0, bar * 1.05, vel=2, gain=0.55, pan=-0.25)
        if b % 2 == 1: mx.note(nm(root), t0 + 2 * beat, bar / 2, vel=2, gain=0.30, pan=-0.2)
        # slow broken chord in the right hand (eighth-note triplets feel, thinned)
        arp = [tones[0] + 12, tones[1] + 12, tones[2] + 12, tones[1] + 24, tones[2] + 12, tones[1] + 12]
        for i, m in enumerate(arp):
            if (b // 4) % 2 == 0 and i % 2 == 1 and b % 4 == 0: continue   # leave air in the first phrase
            mx.note(nm(m), t0 + i * (2 * beat / 3) * 1.5, 1.8, vel=2, gain=0.26, pan=0.15 + 0.1 * (i % 3))
    # melody: a few long tones over the top, second half only (sparse), then a rising answer
    mel = [(4, 'A5', 3), (5, 'F5', 3), (6, 'D5', 4), (7, 'E5', 2), (8, 'D5', 4), (9, 'F5', 2), (10, 'G5', 4),
           (11, 'A5', 3), (12, 'D6', 3), (13, 'C6', 3), (14, 'Bb5', 4), (15, 'A5', 5)]
    for b, n, d in mel:
        mx.note(n.replace('Bb', 'A#'), b * bar + beat * 0.5, d * beat * 1.2, vel=3, gain=0.34, pan=0.3)
    # distant bell on bar starts of phrases
    for b in (0, 8):
        mx.hit(f'{KX}/impact_bell_heavy_002.ogg', b * bar + 0.02, gain=0.16, speed=0.75, pan=-0.4)
    mx.bed(f'{OCU}/DSGNDron_DroneCreepy_OS_02.ogg', 0.07)
    finish(mx, loop_len, 'menu', wet=0.42, rv=4.2)

# BATTLE A: "Rising Tide" - driving D minor ostinato, taiko-ish low hits, bell accents.
def battle(name, root_pc, bpm, bars, seed_bump=0):
    beat = 60 / bpm
    bar = 4 * beat
    loop_len = bars * bar
    mx = Mix(loop_len + 10)
    r = root_pc  # midi of tonic in octave 2
    # progression in semitone offsets from tonic: i, i, bVI, bVII, i, i, iv, V(dom)
    degs = [(0, 'm'), (0, 'm'), (8, 'M'), (10, 'M'), (0, 'm'), (0, 'm'), (5, 'm'), (7, 'dom')]
    for b in range(bars):
        off, kind = degs[b % 8]
        root = r + off
        tones = chord(root + 24, kind)
        t0 = b * bar
        intense = (b // 8) % 2 == 1
        # left hand: driving eighth-note pedal (root / fifth alternating), two octaves down
        for i in range(8):
            m = root + 12 if i % 4 != 3 else root + 19
            if i in (0, 4): m = root + 12
            if i == 0: mx.note(nm(root), t0, beat * 1.6, vel=2, gain=0.30, pan=-0.3)   # one deep root per bar
            mx.note(nm(m), t0 + i * beat / 2, beat * 0.42, vel=3 if i % 4 == 0 else 2, gain=0.42 if i % 4 == 0 else 0.26, pan=-0.3)
        # right hand: chord stab on 1 and the "and" of 2, octave up in the intense half
        if b % 2 == 0 or intense:
            for m in tones: mx.note(nm(m + (12 if intense else 0)), t0, beat * 0.9, vel=3, gain=0.34, pan=0.2)
        for m in tones[:3]: mx.note(nm(m + (12 if intense else 0)), t0 + 2.5 * beat, beat * 0.7, vel=3, gain=0.26, pan=0.2)
        # melody cell, rising over the dominant bars
        if b % 8 in (6, 7) or intense:
            cell = [tones[2] + 12, tones[1] + 12, tones[0] + 24, tones[1] + 12] if not intense else [tones[0] + 24, tones[2] + 12, tones[1] + 24, tones[0] + 24]
            for i, m in enumerate(cell):
                mx.note(nm(m), t0 + i * beat, beat * 0.9, vel=3, gain=0.34, pan=0.35)
        # percussion: low drum (pitched-down wood impact) on 1 and 3, soft ticks on the offbeats, bell every 4 bars
        mx.hit(f'{KX}/impact_wood_heavy_001.ogg', t0, gain=0.40, speed=0.8, pan=0)
        mx.hit(f'{KX}/impact_wood_heavy_003.ogg', t0 + 2 * beat, gain=0.28, speed=0.8)
        if intense:
            mx.hit(f'{KX}/impact_wood_heavy_001.ogg', t0 + 3.5 * beat, gain=0.28, speed=0.8)
            for i in range(4): mx.hit(f'{KX}/impact_wood_light_00{i % 3}.ogg', t0 + (i + 0.5) * beat, gain=0.14, speed=1.1, pan=0.2)
        if b % 4 == 0:
            mx.hit(f'{KX}/impact_bell_heavy_00{(b // 4) % 3}.ogg', t0, gain=0.14, speed=0.6 if not intense else 0.75, pan=-0.2)
    mx.bed(f'{OCU}/DSGNDron_DroneCreepy_OS_01.ogg', 0.05)
    finish(mx, loop_len, name, wet=0.26, rv=2.6)

if __name__ == '__main__':
    which = sys.argv[2] if len(sys.argv) > 2 else 'all'
    if which in ('all', 'menu'): menu()
    if which in ('all', 'battle'):
        battle('battle_a', 38, 92, 16)    # D2 tonic, ~42s loop
        battle('battle_b', 43, 104, 16)   # G2 tonic, ~37s loop
