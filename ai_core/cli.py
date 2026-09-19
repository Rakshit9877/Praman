"""ai_core/cli.py — Simple command-line interface for ai_core.

Usage:
    AI_MODE=mock PYTHONPATH=. python -m ai_core.cli register <image> [--target NAME]
    AI_MODE=mock PYTHONPATH=. python -m ai_core.cli voice <audio>
    AI_MODE=mock PYTHONPATH=. python -m ai_core.cli voice --transcript "Mera naam Rakesh..."

Prints pretty-printed JSON to stdout.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys


def _pretty(obj) -> str:
    """Return indented JSON from a pydantic model or plain dict."""
    if hasattr(obj, "model_dump"):
        data = obj.model_dump(mode="json")
    else:
        data = obj
    return json.dumps(data, ensure_ascii=False, indent=2)


async def _cmd_register(image: str, target: str | None) -> None:
    from ai_core.api import read_register

    def _progress(stage: str, frac: float) -> None:
        print(f"  [{frac:5.0%}] {stage}", file=sys.stderr)

    result = await read_register(image, target_name=target, progress=_progress)
    print(_pretty(result))


async def _cmd_voice(audio: str | None, transcript: str | None) -> None:
    from ai_core.api import process_voice

    def _progress(stage: str, frac: float) -> None:
        print(f"  [{frac:5.0%}] {stage}", file=sys.stderr)

    result = await process_voice(audio, transcript_override=transcript, progress=_progress)
    print(_pretty(result))


def main() -> None:
    parser = argparse.ArgumentParser(prog="ai_core.cli", description="Praman AI core CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    reg = sub.add_parser("register", help="Read a hazri register image")
    reg.add_argument("image", help="Path to the register image")
    reg.add_argument("--target", default=None, help="Worker name to search for")

    voi = sub.add_parser("voice", help="Process a voice note")
    voi.add_argument("audio", nargs="?", default=None, help="Path to the audio file")
    voi.add_argument("--transcript", default=None, help="Pre-supplied text (skips ASR)")

    args = parser.parse_args()

    if args.command == "register":
        asyncio.run(_cmd_register(args.image, args.target))
    elif args.command == "voice":
        if args.audio is None and args.transcript is None:
            parser.error("voice requires either an audio path or --transcript")
        asyncio.run(_cmd_voice(args.audio, args.transcript))


if __name__ == "__main__":
    main()
