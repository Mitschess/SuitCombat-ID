"""
generate_audio.py — Synthesised chiptune music + sound effects for Suit Combat ID.

  assets/music/menu.wav     looping title / menu theme (A minor, 110 BPM)
  assets/music/battle.wav   looping fight theme (D minor, 150 BPM)
  assets/sounds/*.wav       UI + fight sound effects

Everything is generated from code (no samples), so it is free to use.
Run:  python generate_audio.py
"""
import os
import wave
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
SOUNDS = os.path.join(ROOT, "assets", "sounds")
MUSIC = os.path.join(ROOT, "assets", "music")
SR = 22050
rng = np.random.default_rng(7)


# ---------------------------------------------------------------------------
# Synth building blocks
# ---------------------------------------------------------------------------
def t_axis(dur):
    return np.arange(int(SR * dur)) / SR


def midi_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def phase_of(freq, dur):
    """Phase for a constant or per-sample frequency array."""
    f = np.broadcast_to(np.asarray(freq, dtype=float), (int(SR * dur),))
    return np.cumsum(f) / SR


def square(freq, dur, duty=0.5):
    return np.where((phase_of(freq, dur) % 1.0) < duty, 1.0, -1.0)


def triangle(freq, dur):
    p = phase_of(freq, dur) % 1.0
    return 4 * np.abs(p - 0.5) - 1


def sine(freq, dur):
    return np.sin(2 * np.pi * phase_of(freq, dur))


def noise(dur):
    return rng.uniform(-1, 1, int(SR * dur))


def env(dur, attack=0.005, decay=0.1, sustain=0.6, release=0.05):
    n = int(SR * dur)
    e = np.full(n, sustain)
    a, d, r = int(SR * attack), int(SR * decay), int(SR * release)
    a = min(a, n)
    e[:a] = np.linspace(0, 1, a, endpoint=False) if a else e[:a]
    d_end = min(n, a + d)
    e[a:d_end] = np.linspace(1, sustain, d_end - a, endpoint=False)
    if r:
        r = min(r, n)
        e[n - r:] *= np.linspace(1, 0, r)
    return e


def expdecay(dur, rate):
    return np.exp(-rate * t_axis(dur))


def sweep(f0, f1, dur, curve=1.0):
    x = np.linspace(0, 1, int(SR * dur)) ** curve
    return f0 + (f1 - f0) * x


def lowpass(x, k=0.2):
    """One-pole low-pass filter (k small = darker)."""
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc)
        y[i] = acc
    return y


def mix_into(buf, sig, start):
    start = int(start)
    end = min(len(buf), start + len(sig))
    if end > start:
        buf[start:end] += sig[:end - start]


def write_wav(path, sig, peak=0.85):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m = np.max(np.abs(sig)) or 1.0
    data = (sig / m * peak * 32767).astype(np.int16)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


# ---------------------------------------------------------------------------
# Music
# ---------------------------------------------------------------------------
def drum_kick():
    d = 0.18
    return sine(sweep(150, 40, d, 0.5), d) * expdecay(d, 22)


def drum_snare():
    d = 0.16
    return (lowpass(noise(d), 0.5) * 0.8 + sine(190, d) * 0.3) * expdecay(d, 26)


def drum_hat():
    d = 0.04
    n = noise(d)
    return (n - lowpass(n, 0.3)) * expdecay(d, 90)


def song(bpm, bars, chords, melody, bass_pattern, lead_duty=0.25, drums="rock"):
    beat = 60.0 / bpm
    eighth = beat / 2
    total = bars * 4 * beat
    out = np.zeros(int(SR * total))

    # melody: list of bars, each a list of (midi, eighths); midi 0 = rest
    pos = 0.0
    for bar in melody:
        for note, length in bar:
            dur = length * eighth
            if note:
                s = square(midi_hz(note), dur, lead_duty) * env(dur, 0.005, 0.08, 0.55, 0.04) * 0.22
                vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t_axis(dur))
                s = s * vib
                mix_into(out, s, pos * SR)
                # soft echo one eighth later
                mix_into(out, s * 0.25, (pos + eighth * 1.5) * SR)
            pos += dur

    # bass + arpeggio per chord (one chord per bar)
    for b in range(bars):
        root, third, fifth = chords[b % len(chords)]
        bar_t = b * 4 * beat
        for i, step in enumerate(bass_pattern):
            note = {"R": root, "F": fifth, "O": root + 12, "-": None}[step]
            if note is None:
                continue
            dur = eighth * 0.9
            s = triangle(midi_hz(note - 24), dur) * env(dur, 0.003, 0.05, 0.7, 0.02) * 0.45
            mix_into(out, s, (bar_t + i * eighth) * SR)
        arp = [root, third, fifth, root + 12]
        for i in range(16):
            dur = beat / 4 * 0.8
            s = square(midi_hz(arp[i % 4] + 12), dur, 0.125) * env(dur, 0.002, 0.03, 0.3, 0.01) * 0.06
            mix_into(out, s, (bar_t + i * beat / 4) * SR)

        # drums
        for q in range(4):
            t0 = bar_t + q * beat
            if drums == "rock":
                if q in (0, 2):
                    mix_into(out, drum_kick() * 0.7, t0 * SR)
                if q in (1, 3):
                    mix_into(out, drum_snare() * 0.4, t0 * SR)
            else:  # driving: kick every beat
                mix_into(out, drum_kick() * 0.7, t0 * SR)
                if q in (1, 3):
                    mix_into(out, drum_snare() * 0.45, t0 * SR)
            for h in range(2):
                mix_into(out, drum_hat() * 0.15, (t0 + h * eighth) * SR)
    return out


def build_music():
    # --- Menu: A minor, Am F G Em, heroic & calm
    am, f, g, em = (57, 60, 64), (53, 57, 60), (55, 59, 62), (52, 55, 59)
    menu_a = [
        [(69, 2), (72, 1), (76, 1), (74, 1), (72, 1), (71, 1), (72, 1)],
        [(65, 2), (69, 1), (72, 1), (77, 2), (76, 1), (74, 1)],
        [(67, 2), (71, 1), (74, 1), (79, 2), (77, 1), (76, 1)],
        [(76, 3), (74, 1), (71, 2), (67, 2)],
    ]
    menu_b = [
        [(81, 2), (79, 1), (76, 1), (77, 2), (76, 2)],
        [(77, 1), (76, 1), (74, 1), (72, 1), (74, 2), (72, 2)],
        [(71, 1), (72, 1), (74, 1), (76, 1), (79, 2), (74, 2)],
        [(76, 4), (0, 2), (71, 2)],
    ]
    menu = song(110, 16, [am, f, g, em], menu_a + menu_b + menu_a + menu_b,
                ["R", "-", "F", "R", "-", "R", "F", "O"], lead_duty=0.5, drums="rock")
    write_wav(os.path.join(MUSIC, "menu.wav"), menu, 0.7)

    # --- Battle: D minor, Dm Bb C A, fast & driving
    dm, bb, c, a = (62, 65, 69), (58, 62, 65), (60, 64, 67), (57, 61, 64)
    battle_a = [
        [(74, 1), (74, 1), (77, 1), (74, 1), (81, 2), (79, 1), (77, 1)],
        [(77, 1), (77, 1), (74, 1), (77, 1), (82, 2), (81, 1), (79, 1)],
        [(79, 1), (79, 1), (76, 1), (79, 1), (84, 2), (82, 1), (79, 1)],
        [(81, 3), (79, 1), (76, 2), (73, 2)],
    ]
    battle_b = [
        [(86, 2), (84, 1), (81, 1), (82, 2), (81, 2)],
        [(82, 1), (81, 1), (79, 1), (77, 1), (79, 2), (74, 2)],
        [(76, 1), (77, 1), (79, 1), (81, 1), (84, 2), (79, 2)],
        [(81, 2), (85, 2), (88, 2), (0, 2)],
    ]
    battle = song(150, 16, [dm, bb, c, a], battle_a + battle_b + battle_a + battle_b,
                  ["R", "R", "O", "R", "R", "O", "F", "O"], lead_duty=0.25, drums="drive")
    write_wav(os.path.join(MUSIC, "battle.wav"), battle, 0.7)


# ---------------------------------------------------------------------------
# Sound effects
# ---------------------------------------------------------------------------
def jingle(notes, step, duty=0.5, tail=0.4):
    total = len(notes) * step + tail
    out = np.zeros(int(SR * total))
    for i, chord in enumerate(notes):
        for n in (chord if isinstance(chord, tuple) else (chord,)):
            dur = step + (tail if i == len(notes) - 1 else 0.02)
            s = square(midi_hz(n), dur, duty) * env(dur, 0.005, 0.1, 0.5, 0.08) * 0.3
            mix_into(out, s, i * step * SR)
    return out


def build_sfx():
    fx = {}
    # UI
    fx["move"] = square(sweep(880, 1320, 0.05), 0.05, 0.25) * env(0.05, 0.001, 0.02, 0.5, 0.02)
    fx["select"] = np.concatenate([square(660, 0.06, 0.5) * env(0.06, 0.001, 0.02, 0.6, 0.01),
                                   square(990, 0.1, 0.5) * env(0.1, 0.001, 0.03, 0.6, 0.05)])
    fx["back"] = np.concatenate([square(660, 0.06, 0.5) * env(0.06, 0.001, 0.02, 0.6, 0.01),
                                 square(440, 0.1, 0.5) * env(0.1, 0.001, 0.03, 0.6, 0.05)])
    # Fight
    d = 0.14
    fx["punch"] = lowpass(noise(d), 0.35) * expdecay(d, 30) * 0.7 + sine(sweep(160, 50, d), d) * expdecay(d, 20)
    d = 0.2
    whoosh = lowpass(noise(d), 0.15) * np.sin(np.linspace(0, np.pi, int(SR * d))) * 0.8
    fx["kick"] = whoosh + np.pad(sine(sweep(140, 45, 0.12), 0.12) * expdecay(0.12, 22), (int(SR * 0.08), 0))[:len(whoosh)]
    d = 0.25
    crack = noise(d) * expdecay(d, 40)
    fx["hit"] = np.tanh((crack * 0.8 + sine(sweep(120, 38, d), d) * expdecay(d, 12)) * 2.2)
    d = 0.35
    clang = sum(sine(f, d) * expdecay(d, r) for f, r in ((523, 9), (1307, 14), (2093, 20), (2794, 26)))
    fx["block"] = clang * 0.4 + noise(d) * expdecay(d, 120) * 0.5
    d = 0.28
    fx["shoot"] = square(sweep(1400, 180, d, 0.6) * (1 + 0.05 * np.sin(2 * np.pi * 30 * t_axis(d))), d, 0.3) * expdecay(d, 8)
    d = 0.14
    fx["jump"] = square(sweep(220, 660, d, 0.7), d, 0.5) * env(d, 0.002, 0.05, 0.6, 0.05)
    d = 1.0
    fx["ko"] = np.tanh((lowpass(noise(d), 0.08) * 1.5 + sine(sweep(90, 28, d), d)) * expdecay(d, 3.5) * 2.5)
    fx["ready"] = jingle([(57, 64), (60, 67)], 0.18, 0.5, 0.25)
    fight = jingle([(62, 69, 74)], 0.1, 0.5, 0.5)
    fx["fight"] = fight + np.pad(noise(0.3) * expdecay(0.3, 12) * 0.5, (0, len(fight) - int(SR * 0.3)))
    d = 0.45
    chime = np.zeros(int(SR * d))
    for i, n in enumerate((72, 76, 79, 84)):
        seg = triangle(midi_hz(n), d - i * 0.07) * expdecay(d - i * 0.07, 7) * 0.5
        mix_into(chime, seg, i * 0.07 * SR)
    fx["ulti_ready"] = chime
    fx["ulti_cast"] = np.tanh((square(sweep(200, 1200, 0.5, 0.5), 0.5, 0.5) * 0.4 + noise(0.5) * 0.3) * expdecay(0.5, 3) * 2)
    fx["victory"] = jingle([(60, 64, 67), (64, 67, 72), (67, 71, 74), (72, 76, 79), (72, 76, 79)], 0.16, 0.5, 0.8)
    fx["defeat"] = jingle([(64, 67, 71), (62, 65, 69), (60, 63, 67), (55, 59, 62)], 0.28, 0.5, 0.9)
    d = 0.5
    heal = np.zeros(int(SR * d))
    for i, n in enumerate((72, 76, 79, 84, 88)):
        seg = triangle(midi_hz(n), d - i * 0.06) * expdecay(d - i * 0.06, 9) * 0.45
        seg += square(midi_hz(n + 12), d - i * 0.06, 0.125) * expdecay(d - i * 0.06, 16) * 0.12
        mix_into(heal, seg, i * 0.06 * SR)
    fx["heal"] = heal
    for name, sig in fx.items():
        write_wav(os.path.join(SOUNDS, f"{name}.wav"), sig, 0.8)
    return list(fx)


def main():
    names = build_sfx()
    build_music()
    print("SFX:", ", ".join(names))
    print("Music: menu.wav, battle.wav")


if __name__ == "__main__":
    main()
