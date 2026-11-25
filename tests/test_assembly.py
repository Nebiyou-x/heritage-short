import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline.stages.assemble import (
    _format_srt_time,
    _validate_narration_duration,
    run_assemble_stage,
)
from pipeline.stages.music import run_music_stage
from pipeline.validate import validate_storyboard


ROOT = Path(__file__).resolve().parents[1]


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.storyboard = json.loads((ROOT / "storyboard.json").read_text(encoding="utf-8"))

    def test_srt_timestamp_carries_rounded_milliseconds(self):
        self.assertEqual(_format_srt_time(59.9998), "00:01:00,000")

    @patch("pipeline.stages.assemble.probe_media", return_value={
        "format": {"duration": "8.5"},
    })
    def test_long_narration_is_rejected_instead_of_truncated(self, _probe):
        with self.assertRaisesRegex(ValueError, "longer than its 8.00s shot"):
            _validate_narration_duration(Path("voice.wav"), "shot_01", 8)

    @patch("pipeline.stages.assemble.is_mock_mode", return_value=True)
    @patch("pipeline.stages.assemble.log_run")
    def test_mock_assembly_never_creates_fake_video_exports(self, _log_run, _mock_mode):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            with patch("pipeline.stages.assemble.OUTPUTS_DIR", output_dir):
                exports = run_assemble_stage(
                    self.storyboard,
                    {},
                    {},
                    {"cue_main_comedy": "mock-track"},
                    {},
                )

            self.assertEqual(set(exports), {"16:9", "9:16"})
            self.assertTrue(all(not Path(path).exists() for path in exports.values()))
            manifests = list(output_dir.glob("edit_manifest_*.json"))
            self.assertEqual(len(manifests), 1)
            manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["total_duration_sec"],
                sum(shot["duration_sec"] for shot in self.storyboard["shots"]) + 4,
            )

    @patch("pipeline.stages.assemble.is_mock_mode", return_value=True)
    @patch("pipeline.stages.assemble.log_run")
    def test_subtitle_changes_invalidate_assembly_cache(self, _log_run, _mock_mode):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            storyboard = copy.deepcopy(self.storyboard)
            with patch("pipeline.stages.assemble.OUTPUTS_DIR", output_dir):
                original = run_assemble_stage(storyboard, {}, {}, {"cue": "music"}, {})
                storyboard["shots"][0]["subtitle_en"] += " Updated."
                updated = run_assemble_stage(storyboard, {}, {}, {"cue": "music"}, {})

            self.assertNotEqual(original["16:9"], updated["16:9"])

    def test_project_storyboard_still_validates(self):
        validated = validate_storyboard(
            ROOT / "storyboard.json",
            ROOT / "schema" / "storyboard.schema.json",
        )
        self.assertEqual(validated["project_title"], self.storyboard["project_title"])


class MusicStageTests(unittest.TestCase):
    @patch("pipeline.stages.music.is_mock_mode", return_value=False)
    @patch("pipeline.stages.music.probe_media", return_value={
        "streams": [{"codec_type": "audio"}],
    })
    @patch("pipeline.stages.music.log_run")
    def test_copies_and_records_user_track(self, log_run, _probe, _mock_mode):
        storyboard = json.loads((ROOT / "storyboard.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "score.wav"
            source.write_bytes(b"licensed-audio")
            output_dir = root / "outputs"
            with (
                patch("pipeline.stages.music.OUTPUTS_DIR", output_dir),
                patch.dict("os.environ", {
                    "MUSIC_FILE": str(source),
                    "MUSIC_LICENSE": "User licensed",
                }),
            ):
                result = run_music_stage(storyboard)

            target = Path(result["cue_main_comedy"])
            self.assertEqual(target.read_bytes(), b"licensed-audio")
            self.assertEqual(log_run.call_args.args[0]["parameters"]["license"], "User licensed")

    @patch("pipeline.stages.music.is_mock_mode", return_value=False)
    @patch.dict("os.environ", {"MUSIC_FILE": "", "MUSIC_LICENSE": "licensed"})
    def test_requires_music_file_before_production(self, _mock_mode):
        storyboard = json.loads((ROOT / "storyboard.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pipeline.stages.music.OUTPUTS_DIR", Path(temp_dir)):
                with self.assertRaisesRegex(RuntimeError, "MUSIC_FILE"):
                    run_music_stage(storyboard)


if __name__ == "__main__":
    unittest.main()
