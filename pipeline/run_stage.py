import argparse
from pathlib import Path

from dotenv import load_dotenv

from pipeline.common import ensure_dirs
from pipeline.stages.keyframes import run_keyframes_stage
from pipeline.stages.narration import run_narration_stage
from pipeline.validate import validate_storyboard


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one connected provider stage.")
    parser.add_argument("stage", choices=("keyframes", "narration"))
    parser.add_argument("--storyboard", type=Path, default=Path("storyboard.json"))
    parser.add_argument("--schema", type=Path, default=Path("schema/storyboard.schema.json"))
    args = parser.parse_args()

    load_dotenv()
    ensure_dirs()
    storyboard = validate_storyboard(args.storyboard, args.schema)
    if args.stage == "keyframes":
        results = run_keyframes_stage(storyboard)
    else:
        results = run_narration_stage(storyboard)

    print(f"{args.stage} stage complete:")
    for item_id, path in results.items():
        print(f"  {item_id}: {path}")


if __name__ == "__main__":
    main()
