# 🎵 YouTube Audio Downloader + Slowed & Reverb Processor

A two-script toolkit for downloading audio from YouTube and applying slowed + reverb effects — no DAW required.

---

## 📦 Scripts

| Script | Purpose |
|---|---|
| `music.py` | Download audio from YouTube videos or playlists using `yt-dlp` |
| `slowed_reverb.py` | Apply slowed playback, pitch shift, bass boost, and reverb to any audio file |

---

## ⚙️ Requirements

### Python
Python 3.10 or newer (uses `str | None` union syntax).

### For `music.py`
```bash
pip install yt-dlp
```

**FFmpeg** is required for MP3/FLAC/WAV conversion:
- Download: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
- Either add FFmpeg to your system PATH, or pass `--ffmpeg-location "C:\path\to\ffmpeg\bin"` at runtime.

### For `slowed_reverb.py`
```bash
pip install librosa soundfile numpy scipy
```

No FFmpeg needed for WAV/FLAC/OGG output.

---

## 🚀 Usage

### `music.py` — Download Audio from YouTube

```bash
# Basic MP3 download
python music.py https://youtu.be/dQw4w9WgXcQ

# MP3 at 320kbps with a cookies file
python music.py https://youtu.be/ID -f mp3 -q 320 --cookies-file cookies.txt

# Keep original format (no FFmpeg needed)
python music.py https://youtu.be/ID -f best --cookies-file cookies.txt

# Save to a specific folder
python music.py https://youtu.be/ID -f mp3 -o ~/Music --cookies-file cookies.txt

# Point to FFmpeg manually
python music.py https://youtu.be/ID -f mp3 --ffmpeg-location "C:\ffmpeg\bin"
```

**Options:**

| Flag | Default | Description |
|---|---|---|
| `-o`, `--output-dir` | `.` | Output directory |
| `-f`, `--format` | `mp3` | Audio format: `mp3`, `m4a`, `opus`, `wav`, `flac`, `best` |
| `-q`, `--quality` | `192` | Bitrate in kbps or VBR level (0=best, 9=worst) |
| `-t`, `--template` | `%(title)s.%(ext)s` | yt-dlp filename template |
| `--ffmpeg-location` | — | Path to folder containing `ffmpeg` and `ffprobe` |
| `--cookies-file` | — | Path to a Netscape-format `cookies.txt` file |
| `--cookies-from-browser` | — | Pull cookies from: `chrome`, `firefox`, `edge`, `brave`, `safari` |
| `-v`, `--verbose` | — | Show detailed yt-dlp output |

---

### `slowed_reverb.py` — Apply Slowed + Reverb Effect

```bash
# Use default "classic" preset
python slowed_reverb.py song.mp3

# Use a named preset
python slowed_reverb.py song.mp3 --preset dreamy

# Full manual control
python slowed_reverb.py song.mp3 --speed 0.85 --pitch -3 --reverb 0.6 --decay 4.0 --bass 5

# Specify output file
python slowed_reverb.py song.mp3 -o song_lofi.wav

# List all available presets
python slowed_reverb.py --list-presets
```

**Options:**

| Flag | Default | Description |
|---|---|---|
| `-o`, `--output` | Auto-named | Output file path |
| `--preset` | `classic` | Named preset (see below) |
| `--speed` | `0.90` | Speed multiplier (e.g. `0.85` = 85% speed) |
| `--pitch` | `-2.0` | Pitch shift in semitones (negative = lower) |
| `--reverb` | `0.45` | Reverb wet/dry mix (0.0 = dry, 1.0 = full wet) |
| `--decay` | `2.5` | Reverb decay time in seconds |
| `--bass` | `3.0` | Bass boost in dB |

---

### 🎛️ Presets

| Preset | Speed | Pitch | Reverb | Decay | Bass | Description |
|---|---|---|---|---|---|---|
| `classic` | 90% | −2 st | 45% | 2.5s | +3 dB | Classic slowed + reverb |
| `dreamy` | 85% | −3 st | 65% | 4.0s | +4 dB | Deep, dreamy and hazy |
| `underwater` | 80% | −4 st | 75% | 5.5s | +6 dB | Deep underwater feel |
| `subtle` | 95% | −1 st | 30% | 1.5s | +2 dB | Barely noticeable slowdown |
| `lofi` | 88% | −2.5 st | 50% | 3.0s | +5 dB | Lo-fi chill vibes |

---

## 🍪 YouTube Authentication (cookies.txt)

YouTube may block downloads with a bot-detection error. Passing your browser cookies resolves this.

**Option A — cookies file:**
Export your YouTube cookies from your browser (e.g. using the *Get cookies.txt LOCALLY* Chrome extension) and pass the file:
```bash
python music.py https://youtu.be/ID --cookies-file cookies.txt
```

**Option B — cookies from browser directly:**
```bash
python music.py https://youtu.be/ID --cookies-from-browser chrome
```

> ⚠️ Keep your `cookies.txt` file private. It grants access to your Google account.

---

## 🔄 Typical Workflow

```bash
# Step 1: Download the track
python music.py https://youtu.be/dQw4w9WgXcQ -f mp3 --cookies-file cookies.txt

# Step 2: Apply slowed + reverb
python slowed_reverb.py "Rick Astley - Never Gonna Give You Up.mp3" --preset dreamy
```

The output will be saved as `Rick Astley - Never Gonna Give You Up_dreamy.wav`.

---

## 📁 Output Formats

- `slowed_reverb.py` outputs **WAV** by default (lossless, no FFmpeg needed).
- If your input is `.flac`, `.ogg`, or `.wav`, the output extension is preserved.
- `music.py` outputs in whatever format you specify (`-f mp3` etc.), requiring FFmpeg for conversion.

---

## 🐛 Troubleshooting

**`ERROR: Sign in to confirm you're not a bot`**
→ Pass `--cookies-file cookies.txt` or `--cookies-from-browser chrome`.

**`FileNotFoundError: ffmpeg`**
→ Install FFmpeg and add it to your PATH, or pass `--ffmpeg-location "C:\ffmpeg\bin"`.

**`ModuleNotFoundError`**
→ Run `pip install yt-dlp` or `pip install librosa soundfile numpy scipy` depending on which script you're using.

**Output is clipping / too loud**
→ `slowed_reverb.py` auto-normalizes the peak to 98% to prevent clipping. If it still sounds distorted, lower `--bass`.

### Performance checks

Disabled reverb (`--reverb 0`) skips impulse generation and FFT convolution.
Unchanged playback speed (`--speed 1`) skips time stretching. Run the numerical
regression tests after installing the audio dependencies:

```bash
python -m unittest discover -s tests -v
```
