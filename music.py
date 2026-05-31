#!/usr/bin/env python3
"""
YouTube Video to Audio Converter
Uses yt-dlp to download and extract audio from YouTube videos.

Requirements:
    pip install yt-dlp

Optional (for MP3/FLAC/WAV conversion):
    Install FFmpeg: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
    Or pass --ffmpeg-location "C:\\path\\to\\ffmpeg\\bin" to skip PATH setup.
"""

import os
import sys
import argparse
import yt_dlp


def download_audio(
    url: str,
    output_dir: str = ".",
    audio_format: str = "mp3",
    audio_quality: str = "192",
    filename_template: str = "%(title)s.%(ext)s",
    cookies_from_browser: str | None = None,
    cookies_file: str | None = None,
    ffmpeg_location: str | None = None,
    verbose: bool = False,
) -> str | None:
    """
    Download audio from a YouTube URL.

    Args:
        url:                   YouTube video or playlist URL.
        output_dir:            Directory to save the audio file(s).
        audio_format:          Target audio format – mp3, m4a, opus, wav, flac, best.
                               Use 'best' to skip re-encoding (fastest, keeps original quality).
        audio_quality:         VBR quality (0=best…9=worst) or CBR kbps (e.g. 192).
        filename_template:     yt-dlp output template (%(title)s, %(id)s, etc.).
        cookies_from_browser:  Browser to pull cookies from: chrome, firefox, edge, brave, safari.
        cookies_file:          Path to a Netscape-format cookies.txt file.
        ffmpeg_location:       Path to folder containing ffmpeg/ffprobe (when not on PATH).
        verbose:               Print detailed yt-dlp logs.

    Returns:
        Path to the first downloaded file, or None on failure.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, filename_template)

    # Build post-processor chain
    postprocessors = []
    if audio_format != "best":
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": audio_quality,
            }
        )
    postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": postprocessors,
        "quiet": not verbose,
        "no_warnings": not verbose,
        "progress_hooks": [_progress_hook],
    }

    # ── FFmpeg location (when not on system PATH) ──────────────────────────
    if ffmpeg_location:
        ydl_opts["ffmpeg_location"] = ffmpeg_location
        print(f"  🔧 FFmpeg location: {ffmpeg_location}")

    # ── Cookie auth (fixes YouTube bot detection) ──────────────────────────
    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)
        print(f"  🍪 Using cookies from: {cookies_from_browser}")
    elif cookies_file:
        if not os.path.isfile(cookies_file):
            print(f"  ⚠️  Cookies file not found: {cookies_file}", file=sys.stderr)
        else:
            ydl_opts["cookiefile"] = cookies_file
            print(f"  🍪 Using cookies file: {cookies_file}")

    downloaded_files: list[str] = []

    def _record_download(info: dict) -> None:
        path = info.get("filepath") or info.get("_filename", "")
        if path:
            downloaded_files.append(path)

    ydl_opts["postprocessor_hooks"] = [
        lambda info: _record_download(info) if info.get("status") == "finished" else None
    ]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n🎵 Fetching: {url}")
            ydl.download([url])
        if downloaded_files:
            print(f"\n✅ Saved to: {downloaded_files[0]}")
            return downloaded_files[0]
        return None
    except yt_dlp.utils.DownloadError as exc:
        print(f"\n❌ Download error: {exc}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"\n❌ Unexpected error: {exc}", file=sys.stderr)
        return None


def _progress_hook(d: dict) -> None:
    """Display a compact download progress bar."""
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "??%").strip()
        speed = d.get("_speed_str", "?? KiB/s").strip()
        eta = d.get("_eta_str", "??s").strip()
        print(f"\r  ⬇  {percent}  │  {speed}  │  ETA {eta}   ", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\r  ✔  Download complete – converting …{' ' * 20}")


# ──────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt_to_audio",
        description="Download audio from YouTube videos or playlists.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic MP3 download
  python yt_to_audio.py https://youtu.be/dQw4w9WgXcQ

  # MP3 320kbps with cookies
  python yt_to_audio.py https://youtu.be/ID -f mp3 -q 320 --cookies-file cookies.txt

  # Point to FFmpeg directly (no PATH setup needed)
  python yt_to_audio.py https://youtu.be/ID -f mp3 --cookies-file cookies.txt --ffmpeg-location "C:\\ffmpeg\\bin"

  # No FFmpeg needed – keep original format
  python yt_to_audio.py https://youtu.be/ID -f best --cookies-file cookies.txt

  # Full example with all options
  python yt_to_audio.py https://youtu.be/ID -f mp3 -q 320 -o ~/Music --cookies-file cookies.txt --ffmpeg-location "C:\\ffmpeg-7.1-essentials_build\\bin"
        """,
    )
    parser.add_argument("url", nargs="+", help="YouTube URL(s) to download")
    parser.add_argument(
        "-o", "--output-dir",
        default=".",
        metavar="DIR",
        help="Directory for output files (default: current directory)",
    )
    parser.add_argument(
        "-f", "--format",
        default="mp3",
        choices=["mp3", "m4a", "opus", "wav", "flac", "best"],
        help="Audio format (default: mp3)",
    )
    parser.add_argument(
        "-q", "--quality",
        default="192",
        metavar="QUALITY",
        help="Audio quality – VBR 0-9 or CBR kbps (default: 192)",
    )
    parser.add_argument(
        "-t", "--template",
        default="%(title)s.%(ext)s",
        metavar="TEMPLATE",
        help="yt-dlp filename template (default: %%(title)s.%%(ext)s)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose yt-dlp output",
    )
    parser.add_argument(
        "--ffmpeg-location",
        metavar="PATH",
        help=(
            'Path to folder containing ffmpeg.exe and ffprobe.exe. '
            'Use when FFmpeg is not on your system PATH. '
            'Example: --ffmpeg-location "C:\\ffmpeg\\bin"'
        ),
    )

    cookie_group = parser.add_mutually_exclusive_group()
    cookie_group.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER",
        choices=["chrome", "firefox", "edge", "brave", "safari", "chromium", "opera"],
        help="Pull cookies from browser to bypass bot detection.",
    )
    cookie_group.add_argument(
        "--cookies-file",
        metavar="FILE",
        help="Path to a Netscape cookies.txt file.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    success = 0
    for url in args.url:
        result = download_audio(
            url=url,
            output_dir=args.output_dir,
            audio_format=args.format,
            audio_quality=args.quality,
            filename_template=args.template,
            cookies_from_browser=args.cookies_from_browser,
            cookies_file=args.cookies_file,
            ffmpeg_location=args.ffmpeg_location,
            verbose=args.verbose,
        )
        if result:
            success += 1

    total = len(args.url)
    print(f"\n{'─' * 50}")
    print(f"Done: {success}/{total} file(s) downloaded successfully.")
    sys.exit(0 if success == total else 1)


if __name__ == "__main__":
    main()