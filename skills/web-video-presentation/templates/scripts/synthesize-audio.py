#!/usr/bin/env python3
"""
synthesize-audio.py — MiniMax TTS API for web-video-presentation.

Reads audio-segments.json and calls MiniMax Text-to-Audio v2 API to produce
one mp3 per segment under public/audio/<chapter>/<N>.mp3.

Prereq:
  1. npm run extract-narrations   (writes audio-segments.json)
  2. Set MINIMAX_API_KEY in environment or project .env file
     Optionally MINIMAX_GROUP_ID if your account requires it

Usage:
  python3 scripts/synthesize-audio.py                  # incremental
  python3 scripts/synthesize-audio.py --force          # overwrite all
  python3 scripts/synthesize-audio.py --voice=<id>     # override voice
  python3 scripts/synthesize-audio.py --list-voices    # show common voices

To use a different TTS backend, see references/AUDIO.md "用户自带 TTS".
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── MiniMax API defaults ──────────────────────────────────────────────────────
MINIMAX_API_URL = "https://api.minimaxi.com/v1/t2a_v2"
DEFAULT_MODEL   = "speech-01-hd"
DEFAULT_VOICE   = "female-tianmei"

COMMON_VOICES = [
    ("female-tianmei",    "甜美女声（默认）"),
    ("female-yujie",      "御姐女声"),
    ("female-shaonv",     "少女音"),
    ("male-qn-qingse",   "青涩男声"),
    ("male-qn-jingying", "精英男声"),
    ("presenter_male",   "播音男声"),
    ("audiobook_female_1", "有声书女声"),
]


def load_dotenv(root: Path) -> None:
    """Load .env from project root into os.environ (skips keys already set)."""
    env_file = root / ".env"
    if not env_file.exists():
        return
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val


def synthesize_one(
    text: str,
    voice: str,
    out_path: Path,
    api_key: str,
    group_id: str,
) -> None:
    """Call MiniMax T2A v2 API and write the mp3 to out_path."""
    url = MINIMAX_API_URL
    if group_id:
        url = f"{url}?GroupId={group_id}"

    payload = {
        "model": DEFAULT_MODEL,
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": voice,
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body_text}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc

    status = result.get("base_resp", {})
    if status.get("status_code", -1) != 0:
        msg = status.get("status_msg", "unknown error")
        raise RuntimeError(f"API error {status.get('status_code')}: {msg}")

    audio_hex = result.get("data", {}).get("audio", "")
    if not audio_hex:
        raise RuntimeError("API returned empty audio")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(bytes.fromhex(audio_hex))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synthesize audio segments using MiniMax TTS API"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-synthesize all segments (overwrite existing mp3 files)"
    )
    parser.add_argument(
        "--voice", default=DEFAULT_VOICE,
        help=f"Voice ID (default: {DEFAULT_VOICE}). Use --list-voices to see options."
    )
    parser.add_argument(
        "--list-voices", action="store_true",
        help="Print common voice IDs and exit"
    )
    args = parser.parse_args()

    if args.list_voices:
        print("常用音色 ID（传给 --voice=<id>）：\n")
        for vid, desc in COMMON_VOICES:
            print(f"  {vid:<28} {desc}")
        print(
            "\n更多音色见 MiniMax 文档：https://platform.minimaxi.com/document/T2A%20V2\n"
            "也可在 MiniMax 控制台试听后选 ID。"
        )
        return 0

    root = Path(__file__).parent.parent
    load_dotenv(root)

    api_key  = os.environ.get("MINIMAX_API_KEY", "").strip()
    group_id = os.environ.get("MINIMAX_GROUP_ID", "").strip()

    if not api_key:
        print(
            "✗ MINIMAX_API_KEY 未设置。\n"
            "\n"
            "  在项目根目录创建 .env 文件（或直接 export）：\n"
            "    MINIMAX_API_KEY=sk-xxxxx\n"
            "    # MINIMAX_GROUP_ID=xxxxxxxx   # 需要时填写\n"
            "\n"
            "  API key 在 https://platform.minimaxi.com 获取。",
            file=sys.stderr,
        )
        return 1

    segments_path = root / "audio-segments.json"
    if not segments_path.exists():
        print(
            f"✗ {segments_path} 不存在。请先运行：npm run extract-narrations",
            file=sys.stderr,
        )
        return 1

    segments = json.loads(segments_path.read_text(encoding="utf-8"))
    out_dir  = root / "public" / "audio"
    total    = len(segments)

    synthesized = skipped = failed = 0

    for i, seg in enumerate(segments, 1):
        chapter  = seg["chapter"]
        step     = seg["step"]
        text     = seg["text"]
        out_path = out_dir / chapter / f"{step}.mp3"
        label    = f"{chapter}/{step}.mp3"

        if out_path.exists() and not args.force:
            skipped += 1
            print(f"[{i:3d}/{total}] {label:<28} skip (exists)")
            continue

        start = time.monotonic()
        try:
            synthesize_one(text, args.voice, out_path, api_key, group_id)
            elapsed = time.monotonic() - start
            synthesized += 1
            print(f"[{i:3d}/{total}] {label:<28} ✓ {elapsed:.1f}s")
        except Exception as exc:
            failed += 1
            print(f"[{i:3d}/{total}] {label:<28} ✗ FAILED: {exc}", file=sys.stderr)

    print(f"\n✓ 完成 — synthesized {synthesized}, skipped {skipped}, failed {failed}")
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
