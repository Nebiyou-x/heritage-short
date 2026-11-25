import copy
import json
import tempfile
import unittest
from pathlib import Path

from pipeline.validate import validate_storyboard


ROOT = Path(__file__).resolve().parents[1]
STORYBOARD_PATH = ROOT / "storyboard.json"
SCHEMA_PATH = ROOT / "schema" / "storyboard.schema.json"


class ValidateStoryboardTests(unittest.TestCase):
    def setUp(self):
        self.storyboard = json.loads(STORYBOARD_PATH.read_text(encoding="utf-8"))

    def validate_copy(self, storyboard):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "storyboard.json"
            path.write_text(json.dumps(storyboard), encoding="utf-8")
            return validate_storyboard(path, SCHEMA_PATH)

    def test_accepts_project_storyboard(self):
        self.assertEqual(self.validate_copy(self.storyboard)["project_title"], self.storyboard["project_title"])

    def test_rejects_duration_outside_film_requirement(self):
        storyboard = copy.deepcopy(self.storyboard)
        for shot in storyboard["shots"]:
            shot["duration_sec"] = 3
        with self.assertRaisesRegex(ValueError, "total duration"):
            self.validate_copy(storyboard)

    def test_end_card_counts_toward_ninety_second_limit(self):
        storyboard = copy.deepcopy(self.storyboard)
        for shot in storyboard["shots"]:
            shot["duration_sec"] = 11
        with self.assertRaisesRegex(ValueError, "including the 4s AI end card"):
            self.validate_copy(storyboard)

    def test_rejects_duplicate_shot_ids(self):
        storyboard = copy.deepcopy(self.storyboard)
        storyboard["shots"][1]["shot_id"] = storyboard["shots"][0]["shot_id"]
        with self.assertRaisesRegex(ValueError, "duplicate ID"):
            self.validate_copy(storyboard)

    def test_rejects_gaps_in_music_coverage(self):
        storyboard = copy.deepcopy(self.storyboard)
        storyboard["music_cues"][0]["start_sec"] = 1
        with self.assertRaisesRegex(ValueError, "score has a gap"):
            self.validate_copy(storyboard)

    def test_rejects_music_that_ends_before_film(self):
        storyboard = copy.deepcopy(self.storyboard)
        storyboard["music_cues"][0]["end_sec"] = 60
        with self.assertRaisesRegex(ValueError, "before the film ends"):
            self.validate_copy(storyboard)


if __name__ == "__main__":
    unittest.main()
