import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator


def validate_storyboard(storyboard_path: Path, schema_path: Path) -> dict:
    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(storyboard), key=lambda e: list(e.path))
    if errors:
        msg = "\n".join(f"- {'/'.join(str(p) for p in e.path) or 'root'}: {e.message}" for e in errors)
        raise ValueError(f"Storyboard validation failed:\n{msg}")
    return storyboard


def main() -> None:
    sb = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("storyboard.json")
    sc = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("schema/storyboard.schema.json")
    validate_storyboard(sb, sc)
    print(f"OK: {sb} is valid against {sc}")


if __name__ == "__main__":
    main()