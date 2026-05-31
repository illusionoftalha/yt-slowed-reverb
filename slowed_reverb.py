#!/usr/bin/env python3
"""
Slowed + Reverb Generator
Applies slowed-down playback, pitch shift, and reverb to any audio file.

Requirements:
    pip install librosa soundfile numpy scipy

Supports: MP3, WAV, FLAC, OGG, M4A, and most common audio formats.

Usage:
    python slowed_reverb.py input.mp3
    python slowed_reverb.py input.mp3 -o output.mp3
    python slowed_reverb.py input.mp3 --speed 0.85 --pitch -3 --reverb 0.6
    python slowed_reverb.py input.mp3 --preset dreamy
    python slowed_reverb.py input.mp3 --preset underwater
"""

import os
import sys
import argparse
import numpy as np
import librosa
import soundfile as sf
from scipy.signal import fftconvolve


# ──────────────────────────────────────────────
#  Presets
# ──────────────────────────────────────────────

PRESETS = {
    "classic": {
        "speed": 0.90,
        "pitch": -2.0,
        "reverb_wet": 0.45,
        "reverb_decay": 2.5,
        "bass_boost": 3.0,
        "description": "Classic slowed + reverb (most popular style)",
    },
    "dreamy": {
        "speed": 0.85,
        "pitch": -3.0,
        "reverb_wet": 0.65,
        "reverb_decay": 4.0,
        "bass_boost": 4.0,
        "description": "Deep, dreamy and hazy",
    },
    "underwater": {
        "speed": 0.80,
        "pitch": -4.0,
        "reverb_wet": 0.75,
        "reverb_decay": 5.5,
        "bass_boost": 6.0,
        "description": "Deep underwater feel",
    },
    "subtle": {
        "speed": 0.95,
        "pitch": -1.0,
        "reverb_wet": 0.30,
        "reverb_decay": 1.5,
        "bass_boost": 2.0,
        "description": "Subtle, barely noticeable slowdown",
    },
    "lofi": {
        "speed": 0.88,
        "pitch": -2.5,
        "reverb_wet": 0.50,
        "reverb_decay": 3.0,
        "bass_boost": 5.0,
        "description": "Lo-fi chill vibes",
    },
}


# ──────────────────────────────────────────────
#  Audio Processing
# ──────────────────────────────────────────────

def make_reverb_ir(sr: int, decay_seconds: float, room_size: float = 0.8) -> np.ndarray:
    """
    Generate a simple exponential-decay impulse response for convolution reverb.
    No external IR files needed.
    """
    length = int(sr * decay_seconds)
    noise = np.random.randn(length)

    # Exponential decay envelope
    t = np.linspace(0, decay_seconds, length)
    envelope = np.exp(-t * (1.0 / (decay_seconds * room_size)))

    # Add early reflections (pre-delay + first reflections)
    ir = noise * envelope
    ir[0] = 1.0  # Direct signal

    # Add a few early reflections
    for delay_ms, gain in [(20, 0.6), (35, 0.4), (55, 0.3), (80, 0.2)]:
        idx = int(sr * delay_ms / 1000)
        if idx < length:
            ir[idx] += gain

    # Normalize
    ir = ir / (np.max(np.abs(ir)) + 1e-8)
    return ir.astype(np.float32)


def apply_reverb(audio: np.ndarray, sr: int, wet: float, decay: float) -> np.ndarray:
    """Apply convolution reverb with dry/wet mix."""
    ir = make_reverb_ir(sr, decay_seconds=decay)

    if audio.ndim == 2:
        # Stereo: apply reverb to each channel
        wet_l = fftconvolve(audio[:, 0], ir, mode="full")[: len(audio)]
        wet_r = fftconvolve(audio[:, 1], ir, mode="full")[: len(audio)]
        wet_signal = np.stack([wet_l, wet_r], axis=1)
    else:
        wet_signal = fftconvolve(audio, ir, mode="full")[: len(audio)]

    # Normalize wet signal to match dry level
    dry_rms = np.sqrt(np.mean(audio ** 2)) + 1e-8
    wet_rms = np.sqrt(np.mean(wet_signal ** 2)) + 1e-8
    wet_signal = wet_signal * (dry_rms / wet_rms)

    return (1.0 - wet) * audio + wet * wet_signal


def apply_bass_boost(audio: np.ndarray, sr: int, gain_db: float) -> np.ndarray:
    """Boost bass frequencies using a simple low-shelf filter."""
    if gain_db == 0:
        return audio

    from scipy.signal import butter, sosfilt

    # Low-shelf: boost everything below ~200 Hz
    sos = butter(2, 200 / (sr / 2), btype="low", output="sos")
    if audio.ndim == 2:
        low_l = sosfilt(sos, audio[:, 0])
        low_r = sosfilt(sos, audio[:, 1])
        low = np.stack([low_l, low_r], axis=1)
    else:
        low = sosfilt(sos, audio)

    gain_linear = 10 ** (gain_db / 20.0) - 1.0
    return audio + gain_linear * low


def process_audio(
    input_path: str,
    output_path: str,
    speed: float = 0.90,
    pitch: float = -2.0,
    reverb_wet: float = 0.45,
    reverb_decay: float = 2.5,
    bass_boost: float = 3.0,
) -> str:
    """
    Apply slowed + reverb processing to an audio file.

    Args:
        input_path:   Path to the input audio file.
        output_path:  Path to save the processed file.
        speed:        Playback speed multiplier (0.5–1.0). Default 0.90 = 90% speed.
        pitch:        Pitch shift in semitones (negative = lower). Default -2.
        reverb_wet:   Reverb wet/dry mix (0.0 = dry, 1.0 = full reverb). Default 0.45.
        reverb_decay: Reverb decay time in seconds. Default 2.5.
        bass_boost:   Bass boost in dB. Default 3.0.

    Returns:
        Path to the output file.
    """
    print(f"\n📂 Loading: {os.path.basename(input_path)}")
    audio, sr = librosa.load(input_path, sr=None, mono=False)

    # librosa loads mono as 1D, stereo as (2, N) — normalize to (N,) or (N, 2)
    if audio.ndim == 2:
        audio = audio.T  # → (N, channels)
        stereo = True
    else:
        stereo = False

    print(f"   Sample rate : {sr} Hz")
    print(f"   Duration    : {len(audio) / sr:.1f}s  →  {len(audio) / sr / speed:.1f}s after slowing")
    print(f"   Channels    : {'Stereo' if stereo else 'Mono'}")

    # ── Step 1: Time stretch (slow down) ──────────────────────────────────
    print(f"\n⏱  Slowing to {speed:.0%} speed …", end=" ", flush=True)
    if stereo:
        left  = librosa.effects.time_stretch(audio[:, 0], rate=speed)
        right = librosa.effects.time_stretch(audio[:, 1], rate=speed)
        audio = np.stack([left, right], axis=1)
    else:
        audio = librosa.effects.time_stretch(audio, rate=speed)
    print("done")

    # ── Step 2: Pitch shift ───────────────────────────────────────────────
    if pitch != 0:
        print(f"🎵  Shifting pitch by {pitch:+.1f} semitones …", end=" ", flush=True)
        if stereo:
            left  = librosa.effects.pitch_shift(audio[:, 0], sr=sr, n_steps=pitch)
            right = librosa.effects.pitch_shift(audio[:, 1], sr=sr, n_steps=pitch)
            audio = np.stack([left, right], axis=1)
        else:
            audio = librosa.effects.pitch_shift(audio, sr=sr, n_steps=pitch)
        print("done")

    # ── Step 3: Bass boost ────────────────────────────────────────────────
    if bass_boost > 0:
        print(f"🔊  Bass boost +{bass_boost:.1f} dB …", end=" ", flush=True)
        audio = apply_bass_boost(audio, sr, bass_boost)
        print("done")

    # ── Step 4: Reverb ────────────────────────────────────────────────────
    print(f"🌊  Applying reverb (wet={reverb_wet:.0%}, decay={reverb_decay:.1f}s) …", end=" ", flush=True)
    audio = apply_reverb(audio, sr, wet=reverb_wet, decay=reverb_decay)
    print("done")

    # ── Normalize output to prevent clipping ──────────────────────────────
    peak = np.max(np.abs(audio))
    if peak > 0.98:
        audio = audio * (0.98 / peak)

    # ── Save ──────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    sf.write(output_path, audio, sr)
    size_mb = os.path.getsize(output_path) / 1_048_576
    print(f"\n✅ Saved: {output_path}  ({size_mb:.1f} MB)")
    return output_path


# ──────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────

def build_output_path(input_path: str, preset: str | None, suffix: str = "") -> str:
    base, ext = os.path.splitext(input_path)
    # Prefer WAV output (lossless, no FFmpeg needed); MP3 needs FFmpeg via soundfile
    out_ext = ext if ext.lower() in (".wav", ".flac", ".ogg") else ".wav"
    tag = f"_{preset}" if preset else "_slowed_reverb"
    tag += suffix
    return f"{base}{tag}{out_ext}"


def build_parser() -> argparse.ArgumentParser:
    preset_list = "\n".join(f"  {k:12s} – {v['description']}" for k, v in PRESETS.items())

    parser = argparse.ArgumentParser(
        prog="slowed_reverb",
        description="Apply slowed + reverb effect to audio files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Presets:
{preset_list}

Examples:
  # Use default classic preset
  python slowed_reverb.py song.mp3

  # Use a named preset
  python slowed_reverb.py song.mp3 --preset dreamy

  # Full manual control
  python slowed_reverb.py song.mp3 --speed 0.85 --pitch -3 --reverb 0.6 --decay 4.0 --bass 5

  # Specify output file
  python slowed_reverb.py song.mp3 -o song_lofi.wav

  # List all presets
  python slowed_reverb.py --list-presets
        """,
    )

    parser.add_argument("input", nargs="?", help="Input audio file path")
    parser.add_argument("-o", "--output", metavar="FILE", help="Output file path")
    parser.add_argument(
        "--preset",
        choices=list(PRESETS.keys()),
        metavar="NAME",
        help=f"Use a preset. Choices: {', '.join(PRESETS.keys())}",
    )

    # Manual controls (override preset values)
    parser.add_argument("--speed",  type=float, metavar="RATE",  help="Speed multiplier, e.g. 0.85 (default: 0.90)")
    parser.add_argument("--pitch",  type=float, metavar="SEMI",  help="Pitch shift in semitones, e.g. -3 (default: -2)")
    parser.add_argument("--reverb", type=float, metavar="WET",   help="Reverb wet mix 0.0–1.0 (default: 0.45)")
    parser.add_argument("--decay",  type=float, metavar="SECS",  help="Reverb decay in seconds (default: 2.5)")
    parser.add_argument("--bass",   type=float, metavar="DB",    help="Bass boost in dB (default: 3.0)")
    parser.add_argument("--list-presets", action="store_true",   help="Print all available presets and exit")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_presets:
        print("\nAvailable presets:\n")
        for name, cfg in PRESETS.items():
            print(f"  {name:12s}  {cfg['description']}")
            print(f"               speed={cfg['speed']}, pitch={cfg['pitch']:+.1f}, "
                  f"reverb={cfg['reverb_wet']}, decay={cfg['reverb_decay']}s, "
                  f"bass=+{cfg['bass_boost']}dB\n")
        sys.exit(0)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    if not os.path.isfile(args.input):
        print(f"❌ File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # ── Resolve settings: preset → then manual overrides ──────────────────
    preset_name = args.preset or "classic"
    cfg = dict(PRESETS[preset_name])

    if args.speed  is not None: cfg["speed"]         = args.speed
    if args.pitch  is not None: cfg["pitch"]         = args.pitch
    if args.reverb is not None: cfg["reverb_wet"]    = args.reverb
    if args.decay  is not None: cfg["reverb_decay"]  = args.decay
    if args.bass   is not None: cfg["bass_boost"]    = args.bass

    output_path = args.output or build_output_path(args.input, args.preset)

    print(f"\n{'─'*50}")
    print(f"  Preset  : {preset_name}  –  {PRESETS[preset_name]['description']}")
    print(f"  Speed   : {cfg['speed']:.0%}")
    print(f"  Pitch   : {cfg['pitch']:+.1f} semitones")
    print(f"  Reverb  : {cfg['reverb_wet']:.0%} wet / {cfg['reverb_decay']}s decay")
    print(f"  Bass    : +{cfg['bass_boost']} dB")
    print(f"{'─'*50}")

    process_audio(
        input_path=args.input,
        output_path=output_path,
        speed=cfg["speed"],
        pitch=cfg["pitch"],
        reverb_wet=cfg["reverb_wet"],
        reverb_decay=cfg["reverb_decay"],
        bass_boost=cfg["bass_boost"],
    )

    print(f"\n{'─'*50}")
    print("Done! 🎧")


if __name__ == "__main__":
    main()
