import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator
from pipeline.common import END_CARD_DURATION_SEC


def _validate_timeline(storyboard: dict) -> None:
    errors = []
    shots = storyboard["shots"]
    total_duration = sum(float(shot["duration_sec"]) for shot in shots)
    final_duration = total_duration + END_CARD_DURATION_SEC

    if not 60 <= final_duration <= 90:
        errors.append(
            f"shots: total duration including the {END_CARD_DURATION_SEC}s AI end card "
            f"is {final_duration:g}s; expected 60-90s"
        )

    for label, items, id_key in (
        ("shots", shots, "shot_id"),
        ("music_cues", storyboard["music_cues"], "id"),
    ):
        seen = set()
        for index, item in enumerate(items):
            item_id = item[id_key]
            if item_id in seen:
                errors.append(f"{label}/{index}/{id_key}: duplicate ID {item_id!r}")
            seen.add(item_id)

    cues = sorted(storyboard["music_cues"], key=lambda cue: cue["start_sec"])
    covered_until = 0.0
    for index, cue in enumerate(cues):
        if cue["end_sec"] <= cue["start_sec"]:
            errors.append(f"music_cues/{index}: end_sec must be greater than start_sec")
        if cue["start_sec"] > covered_until:
            errors.append(
                f"music_cues: score has a gap from {covered_until:g}s "
                f"to {cue['start_sec']:g}s"
            )
        covered_until = max(covered_until, cue["end_sec"])
    if covered_until < total_duration:
        errors.append(
            f"music_cues: score ends at {covered_until:g}s before "
            f"the film ends at {total_duration:g}s"
        )

    if errors:
        raise ValueError("Storyboard validation failed:\n" + "\n".join(f"- {e}" for e in errors))


def validate_storyboard(storyboard_path: Path, schema_path: Path) -> dict:
    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(storyboard), key=lambda e: list(e.path))
    if errors:
        msg = "\n".join(f"- {'/'.join(str(p) for p in e.path) or 'root'}: {e.message}" for e in errors)
        raise ValueError(f"Storyboard validation failed:\n{msg}")
    _validate_timeline(storyboard)
    return storyboard


def main() -> None:
    sb = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("storyboard.json")
    sc = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("schema/storyboard.schema.json")
    validate_storyboard(sb, sc)
    print(f"OK: {sb} is valid against {sc}")


if __name__ == "__main__":
    main()