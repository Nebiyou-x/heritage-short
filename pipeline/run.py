import sys
from pathlib import Path
from dotenv import load_dotenv
from pipeline.common import ensure_dirs
from pipeline.validate import validate_storyboard
from pipeline.stages.keyframes import run_keyframes_stage
from pipeline.stages.shots import run_shots_stage
from pipeline.stages.music import run_music_stage
from pipeline.stages.narration import run_narration_stage
from pipeline.stages.assemble import run_assemble_stage


def main() -> None:
    load_dotenv()
    ensure_dirs()
    sb_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("storyboard.json")
    sc_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("schema/storyboard.schema.json")

    storyboard = validate_storyboard(sb_path, sc_path)
    keyframes = run_keyframes_stage(storyboard)
    shots = run_shots_stage(storyboard, keyframes)
    music = run_music_stage(storyboard)
    narration = run_narration_stage(storyboard)
    exports = run_assemble_stage(storyboard, keyframes, shots, music, narration)

    print("Pipeline complete. Exports:")
    for ar, path in exports.items():
        print(f"  [{ar}] {path}")


if __name__ == "__main__":
    main()