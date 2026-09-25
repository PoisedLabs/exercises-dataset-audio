#!/usr/bin/env python3
"""Generate ElevenLabs MP3 narration for Lift Tracker exercises."""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib import error, request

DEFAULT_MODEL = "eleven_multilingual_v2"
DEFAULT_DATASET = Path(__file__).resolve().parent.parent / "Sources/LiftTrackerCore/Resources/exercises.json"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "audio"
API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def narration_text(exercise: dict) -> str:
    steps = exercise.get("instruction_steps", {}).get("en") or []
    instructions = steps or [exercise.get("instructions", {}).get("en", "")]
    instructions = [step.strip() for step in instructions if step.strip()]
    if not instructions:
        raise ValueError(f"Exercise {exercise.get('id', '<unknown>')} has no English instructions")

    numbered_steps = " ".join(
        f"Step {index}: {step}" for index, step in enumerate(instructions, start=1)
    )
    return f"{exercise['name']}. {numbered_steps}"


def request_audio(api_key: str, voice_id: str, text: str, model_id: str) -> bytes:
    payload = json.dumps(
        {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }
    ).encode("utf-8")
    request_object = request.Request(
        API_URL.format(voice_id=voice_id),
        data=payload,
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
        method="POST",
    )
    with request.urlopen(request_object, timeout=120) as response:
        return response.read()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate one ElevenLabs MP3 for each Lift Tracker exercise."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--voice-id", default=os.getenv("ELEVENLABS_VOICE_ID"))
    parser.add_argument(
        "--model-id", default=os.getenv("ELEVENLABS_MODEL_ID", DEFAULT_MODEL)
    )
    parser.add_argument("--api-key", default=os.getenv("ELEVENLABS_API_KEY"))
    parser.add_argument(
        "--exercise-id",
        action="append",
        help="Generate only this exercise ID. Repeat the option for multiple IDs.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Generate at most this many exercises, useful for a small test batch.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate audio files that already exist.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to wait between API requests.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.api_key:
        print("Missing ELEVENLABS_API_KEY.", file=sys.stderr)
        return 2
    if not args.voice_id:
        print("Missing ELEVENLABS_VOICE_ID.", file=sys.stderr)
        return 2

    with args.dataset.open(encoding="utf-8") as file:
        exercises = json.load(file)

    selected_ids = set(args.exercise_id or [])
    if selected_ids:
        exercises = [exercise for exercise in exercises if exercise.get("id") in selected_ids]
    if args.limit is not None:
        exercises = exercises[: args.limit]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    generated = skipped = failed = 0

    for exercise in exercises:
        exercise_id = exercise.get("id")
        if not exercise_id:
            print("FAILED exercise without an id", file=sys.stderr)
            failed += 1
            continue

        output_path = args.output_dir / f"{exercise_id}.mp3"
        if output_path.exists() and not args.overwrite:
            print(f"SKIP  {output_path}")
            skipped += 1
            continue

        try:
            text = narration_text(exercise)
            print(f"GENERATE  {output_path}")
            output_path.write_bytes(request_audio(args.api_key, args.voice_id, text, args.model_id))
            generated += 1
        except ValueError as exc:
            print(f"FAILED {exercise_id}: {exc}", file=sys.stderr)
            failed += 1
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            print(f"FAILED {exercise_id}: HTTP {exc.code}: {details}", file=sys.stderr)
            failed += 1
        except error.URLError as exc:
            print(f"FAILED {exercise_id}: {exc.reason}", file=sys.stderr)
            failed += 1

        if args.delay > 0:
            time.sleep(args.delay)

    print(f"Done: generated={generated}, skipped={skipped}, failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())