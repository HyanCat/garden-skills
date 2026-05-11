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
  python3 scripts/synthesize-audio.py                    # interactive confirm
  python3 scripts/synthesize-audio.py --yes              # skip confirm prompt
  python3 scripts/synthesize-audio.py --force            # overwrite all
  python3 scripts/synthesize-audio.py --voice=<id>       # override voice
  python3 scripts/synthesize-audio.py --model=<id>       # override model
  python3 scripts/synthesize-audio.py --list-voices      # show all voices and exit

音色列表：https://platform.minimaxi.com/docs/faq/system-voice-id
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
DEFAULT_MODEL   = "speech-2.8-hd"
DEFAULT_VOICE   = "Chinese (Mandarin)_Gentleman"

# (voice_id, 中文说明)  ← 前 10 条在交互选单里编号展示
COMMON_VOICES = [
    ("Chinese (Mandarin)_Gentleman",          "温润男声（默认）"),
    ("Chinese (Mandarin)_Gentle_Youth",        "温润青年"),
    ("Chinese (Mandarin)_Lyrical_Voice",       "抒情男声"),
    ("Chinese (Mandarin)_Radio_Host",          "电台男主播"),
    ("Chinese (Mandarin)_Male_Announcer",      "播报男声"),
    ("Chinese (Mandarin)_Reliable_Executive",  "沉稳高管"),
    ("Chinese (Mandarin)_Sincere_Adult",       "真诚青年"),
    ("Chinese (Mandarin)_News_Anchor",         "新闻女声"),
    ("Chinese (Mandarin)_Warm_Bestie",         "温暖闺蜜"),
    ("Chinese (Mandarin)_Wise_Women",          "阅历姐姐"),
    ("Chinese (Mandarin)_Sweet_Lady",          "甜美女声"),
    ("Chinese (Mandarin)_Warm_Girl",           "温暖少女"),
    ("female-tianmei",                         "甜美女性音色"),
    ("female-yujie",                           "御姐音色"),
    ("male-qn-jingying",                       "精英青年音色"),
    ("male-qn-qingse",                         "青涩青年音色"),
    ("presenter_male",                         "播音男声"),
    ("audiobook_female_1",                     "有声书女声"),
]


# ── .env loader ───────────────────────────────────────────────────────────────
def load_dotenv(root: Path) -> None:
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


# ── interactive confirm ────────────────────────────────────────────────────────
def voice_label(voice_id: str) -> str:
    """Return display name for a voice_id, or just the id if unknown."""
    for vid, desc in COMMON_VOICES:
        if vid == voice_id:
            return desc
    return voice_id


def interactive_confirm(model: str, voice: str) -> tuple:
    """
    Ask the user to confirm or change the model/voice before synthesizing.
    Returns (model, voice) — possibly updated by user input.
    Raises SystemExit if user quits.
    """
    print()
    print("─" * 58)
    print("  合成配置确认")
    print(f"  模型：{model}")
    print(f"  音色：{voice}  {voice_label(voice)}")
    print("─" * 58)
    print()
    print("  常用音色（输入编号切换，直接回车确认）：")
    print()
    for i, (vid, desc) in enumerate(COMMON_VOICES, 1):
        marker = "▶" if vid == voice else " "
        print(f"   {marker} {i:2d}.  {vid:<44} {desc}")
    print()
    print("  其它操作：  m — 手动输入模型  /  v — 手动输入音色 ID  /  q — 退出")
    print()

    while True:
        try:
            raw = input("  请选择 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if raw == "":
            # confirm as-is
            break
        elif raw.lower() == "q":
            print("已退出。")
            sys.exit(0)
        elif raw.lower() == "m":
            try:
                new_model = input(f"  新模型 ID（当前 {model}）> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(0)
            if new_model:
                model = new_model
                print(f"  ✓ 模型已设为：{model}")
            break
        elif raw.lower() == "v":
            try:
                new_voice = input(f"  新音色 ID（当前 {voice}）> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(0)
            if new_voice:
                voice = new_voice
                print(f"  ✓ 音色已设为：{voice}  {voice_label(voice)}")
            break
        elif raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(COMMON_VOICES):
                voice = COMMON_VOICES[idx][0]
                print(f"  ✓ 音色已设为：{voice}  {voice_label(voice)}")
                break
            else:
                print(f"  ✗ 编号超出范围（1–{len(COMMON_VOICES)}），请重新输入。")
        else:
            print("  ✗ 无效输入，请输入编号、m、v 或直接回车。")

    print()
    return model, voice


# ── TTS call ──────────────────────────────────────────────────────────────────
def synthesize_one(
    text: str,
    model: str,
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
        "model": model,
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


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synthesize audio segments using MiniMax TTS API"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-synthesize all segments (overwrite existing mp3 files)"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip interactive confirmation and use default/provided model+voice"
    )
    parser.add_argument(
        "--voice", default=None,
        help=f"Voice ID (default: {DEFAULT_VOICE}). Run --list-voices to see options."
    )
    parser.add_argument(
        "--model", default=None,
        help=f"Model ID (default: {DEFAULT_MODEL})."
    )
    parser.add_argument(
        "--list-voices", action="store_true",
        help="Print common voice IDs and exit"
    )
    args = parser.parse_args()

    if args.list_voices:
        print(f"\n音色列表（共 {len(COMMON_VOICES)} 条常用音色）：\n")
        for i, (vid, desc) in enumerate(COMMON_VOICES, 1):
            print(f"  {i:2d}.  {vid:<44} {desc}")
        print(
            "\n完整列表（300+ 音色）：\n"
            "  https://platform.minimaxi.com/docs/faq/system-voice-id\n"
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

    model = args.model or DEFAULT_MODEL
    voice = args.voice or DEFAULT_VOICE

    # Interactive confirmation (skip if --yes, or if stdin is not a tty)
    if not args.yes and sys.stdin.isatty():
        model, voice = interactive_confirm(model, voice)

    segments = json.loads(segments_path.read_text(encoding="utf-8"))
    out_dir  = root / "public" / "audio"
    total    = len(segments)

    print(f"▸ 开始合成  模型={model}  音色={voice}")
    print(f"▸ 共 {total} 段，输出目录：{out_dir}\n")

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
            synthesize_one(text, model, voice, out_path, api_key, group_id)
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
