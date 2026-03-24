from __future__ import annotations

import io
import json
import shutil
import sys
import unittest
import uuid
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app
from audio_metadata.schema import normalize_record_schema_v1


@contextmanager
def workspace_tempdir() -> Path:
    base_dir = PROJECT_ROOT / "tests_tmp"
    base_dir.mkdir(exist_ok=True)
    temp_dir = base_dir / f"tmp_{uuid.uuid4().hex}"
    temp_dir.mkdir()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def make_flat_record(
    *,
    file_name: str,
    source_path: str,
    tempo_bpm: float | None = 90.0,
    tempo_quality: str | None = "low",
    tempo_applicable: bool | None = True,
    is_loop: bool | None = True,
    brightness: str | None = "bright",
    duration_sec: float = 4.0,
) -> dict:
    return {
        "status": "ok",
        "file_name": file_name,
        "source_path": source_path,
        "file_format": Path(source_path).suffix.lstrip("."),
        "tempo_applicable": tempo_applicable,
        "is_loop": is_loop,
        "duration_bucket": "short",
        "brightness": brightness,
        "technical": {
            "duration_sec": duration_sec,
            "sample_rate_hz": 44100,
            "channels": 2,
        },
        "features": {
            "loudness_lufs": -12.0,
            "tempo_bpm": tempo_bpm,
            "tempo_confidence": 0.6,
            "tempo_quality": tempo_quality,
            "spectral_centroid_hz": 4200.0,
            "rms": 0.2,
        },
        "errors": [],
    }


class ReviewBatchAndStatsTests(unittest.TestCase):
    def test_review_batch_preset_restore_bpm_preview_and_apply(self) -> None:
        with workspace_tempdir() as temp_path:
            input_path = temp_path / "library.json"
            output_path = temp_path / "reviewed.json"
            payload = {
                "run": {},
                "files": [
                    make_flat_record(
                        file_name="KSHMR_128_hat_loop_main.wav",
                        source_path=str(temp_path / "loop.wav"),
                        tempo_bpm=None,
                        tempo_quality="not_applicable",
                        tempo_applicable=False,
                        is_loop=True,
                    ),
                    make_flat_record(
                        file_name="KSHMR_hat_texture.wav",
                        source_path=str(temp_path / "texture.wav"),
                        tempo_bpm=None,
                        tempo_quality="not_applicable",
                        tempo_applicable=False,
                        is_loop=True,
                    ),
                ],
            }
            input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            dry_run_stdout = io.StringIO()
            with redirect_stdout(dry_run_stdout):
                exit_code = app.main(
                    [
                        "review-batch",
                        "--input",
                        str(input_path),
                        "--preset",
                        "restore-bpm-from-filename-for-loops",
                    ]
                )

            dry_run_output = dry_run_stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Preset: restore-bpm-from-filename-for-loops", dry_run_output)
            self.assertIn("Matched 1 record(s).", dry_run_output)
            self.assertIn("set derived.tempo_applicable = true", dry_run_output)
            self.assertIn("set features.tempo_bpm = 128.0", dry_run_output)
            self.assertIn('set features.tempo_quality = "low"', dry_run_output)
            self.assertIn("Dry-run only.", dry_run_output)

            apply_stdout = io.StringIO()
            with redirect_stdout(apply_stdout):
                exit_code = app.main(
                    [
                        "review-batch",
                        "--input",
                        str(input_path),
                        "--output",
                        str(output_path),
                        "--preset",
                        "restore-bpm-from-filename-for-loops",
                        "--apply",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Wrote 1 updated record(s)", apply_stdout.getvalue())
            saved_payload = json.loads(output_path.read_text(encoding="utf-8-sig"))
            self.assertEqual(saved_payload["app_version"], "v0.1-b3")
            target_record = next(record for record in saved_payload["files"] if "128_hat_loop" in record["file_name"])
            untouched_record = next(record for record in saved_payload["files"] if "texture" in record["file_name"])
            self.assertTrue(target_record["tempo_applicable"])
            self.assertEqual(target_record["features"]["tempo_bpm"], 128.0)
            self.assertEqual(target_record["features"]["tempo_quality"], "low")
            self.assertEqual(
                target_record["review"]["notes"],
                ["preset: restore-bpm-from-filename-for-loops"],
            )
            self.assertEqual(untouched_record["review"], {})

    def test_review_batch_dry_run_and_apply_updates_only_matched_records(self) -> None:
        with workspace_tempdir() as temp_path:
            input_path = temp_path / "library.json"
            output_path = temp_path / "reviewed.json"
            payload = {
                "run": {},
                "files": [
                    make_flat_record(
                        file_name="KSHMR_108_drum_fill_long_bongo_jam.wav",
                        source_path=str(temp_path / "fill1.wav"),
                        is_loop=True,
                    ),
                    make_flat_record(
                        file_name="KSHMR_128_drum_fill_long_adrenaline.wav",
                        source_path=str(temp_path / "fill2.wav"),
                        is_loop=True,
                    ),
                    make_flat_record(
                        file_name="KSHMR_128_drum_loop_main.wav",
                        source_path=str(temp_path / "loop.wav"),
                        is_loop=True,
                    ),
                ],
            }
            input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            dry_run_stdout = io.StringIO()
            with redirect_stdout(dry_run_stdout):
                exit_code = app.main(
                    [
                        "review-batch",
                        "--input",
                        str(input_path),
                        "--keyword",
                        "fill",
                        "--is-loop",
                        "true",
                        "--set-is-loop",
                        "false",
                        "--set-note",
                        "drum fill path: mark as non-loop",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Matched 2 record(s).", dry_run_stdout.getvalue())
            self.assertIn("Records that would change: 2.", dry_run_stdout.getvalue())
            self.assertIn("Dry-run only.", dry_run_stdout.getvalue())
            unchanged_payload = json.loads(input_path.read_text(encoding="utf-8-sig"))
            self.assertFalse(any("review" in record for record in unchanged_payload["files"]))

            apply_stdout = io.StringIO()
            with redirect_stdout(apply_stdout):
                exit_code = app.main(
                    [
                        "review-batch",
                        "--input",
                        str(input_path),
                        "--output",
                        str(output_path),
                        "--keyword",
                        "fill",
                        "--is-loop",
                        "true",
                        "--set-is-loop",
                        "false",
                        "--set-note",
                        "drum fill path: mark as non-loop",
                        "--apply",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Wrote 2 updated record(s)", apply_stdout.getvalue())
            saved_payload = json.loads(output_path.read_text(encoding="utf-8-sig"))
            self.assertEqual(saved_payload["schema_version"], "v1")
            self.assertEqual(saved_payload["app_version"], "v0.1-b3")

            fill_records = [
                record for record in saved_payload["files"] if "fill" in record["file_name"].casefold()
            ]
            loop_record = next(record for record in saved_payload["files"] if record["file_name"] == "KSHMR_128_drum_loop_main.wav")
            self.assertEqual(len(fill_records), 2)
            for record in fill_records:
                self.assertFalse(record["is_loop"])
                self.assertEqual(record["review"]["notes"], ["drum fill path: mark as non-loop"])
                self.assertFalse(record["review"]["overrides"]["derived"]["is_loop"])
            self.assertEqual(loop_record["review"], {})
            self.assertTrue(loop_record["is_loop"])

    def test_review_batch_requires_a_filter(self) -> None:
        with workspace_tempdir() as temp_path:
            input_path = temp_path / "library.json"
            input_path.write_text(json.dumps({"run": {}, "files": []}, indent=2), encoding="utf-8")

            with self.assertRaises(SystemExit):
                with redirect_stderr(io.StringIO()):
                    app.main(
                        [
                            "review-batch",
                            "--input",
                            str(input_path),
                            "--set-is-loop",
                            "false",
                        ]
                    )

    def test_review_candidates_reports_rules_groups_limit_and_filter(self) -> None:
        with workspace_tempdir() as temp_path:
            input_path = temp_path / "library.json"
            payload = {
                "run": {},
                "files": [
                    make_flat_record(
                        file_name="KSHMR_100_hat_loop.wav",
                        source_path=str(temp_path / "a.wav"),
                        tempo_bpm=None,
                        tempo_applicable=False,
                    ),
                    make_flat_record(
                        file_name="KSHMR_108_drum_fill_long_bongo_jam.wav",
                        source_path=str(temp_path / "b.wav"),
                        is_loop=True,
                    ),
                    make_flat_record(
                        file_name="KSHMR_crash_acoustic_dark.wav",
                        source_path=str(temp_path / "c.wav"),
                        brightness="bright",
                    ),
                    make_flat_record(
                        file_name="KSHMR_128_shaker_loop_mid.wav",
                        source_path=str(temp_path / "d.wav"),
                        tempo_quality="low",
                        tempo_applicable=True,
                        is_loop=True,
                    ),
                ],
            }
            input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = app.main(
                    [
                        "review-candidates",
                        "--input",
                        str(input_path),
                        "--include-rule-d",
                        "--limit",
                        "2",
                    ]
                )

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Found 4 review candidate(s).", output)
            self.assertIn("Rule groups:", output)
            self.assertIn("Rule A: 1", output)
            self.assertIn("Rule B: 1", output)
            self.assertIn("Rule C: 1", output)
            self.assertIn("Rule D: 4", output)
            self.assertIn("Recommended action: restore-bpm-from-filename-for-loops", output)
            self.assertIn("Recommended action: mark-fill-as-non-loop", output)
            self.assertIn("Showing up to 2 example(s) per rule.", output)
            self.assertIn("file_name:", output)
            self.assertIn("current_fields:", output)

            filtered_stdout = io.StringIO()
            with redirect_stdout(filtered_stdout):
                exit_code = app.main(
                    [
                        "review-candidates",
                        "--input",
                        str(input_path),
                        "--rule",
                        "B",
                        "--limit",
                        "1",
                    ]
                )

            filtered_output = filtered_stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Found 1 review candidate(s).", filtered_output)
            self.assertIn("Rule B: 1", filtered_output)
            self.assertNotIn("Rule A:", filtered_output)
            self.assertIn("Showing up to 1 example(s) per rule.", filtered_output)

    def test_review_candidates_rule_b_ignores_filler_substrings(self) -> None:
        with workspace_tempdir() as temp_path:
            input_path = temp_path / "library.json"
            payload = {
                "run": {},
                "files": [
                    make_flat_record(
                        file_name="KSHMR_150_drum_fill_long_energetic.wav",
                        source_path=str(temp_path / "fill.wav"),
                        is_loop=True,
                    ),
                    make_flat_record(
                        file_name="KSHMR_95_drum_loop_marching_snare_big_filler.wav",
                        source_path=str(temp_path / "filler.wav"),
                        is_loop=True,
                    ),
                ],
            }
            input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = app.main(
                    [
                        "review-candidates",
                        "--input",
                        str(input_path),
                        "--limit",
                        "10",
                    ]
                )

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Found 1 review candidate(s).", output)
            self.assertIn("Rule B: 1", output)
            self.assertIn("KSHMR_150_drum_fill_long_energetic.wav", output)
            self.assertNotIn("KSHMR_95_drum_loop_marching_snare_big_filler.wav", output)

    def test_review_stats_summarizes_overrides_notes_sources_and_keywords(self) -> None:
        with workspace_tempdir() as temp_path:
            input_path = temp_path / "library.json"
            payload = {
                "schema_version": "v1",
                "app_version": "v0.1-b3",
                "run": {},
                "files": [
                    normalize_record_schema_v1(
                        {
                            **make_flat_record(
                                file_name="KSHMR_108_drum_fill_long_bongo_jam.wav",
                                source_path=str(temp_path / "fill1.wav"),
                            ),
                            "review": {
                                "overrides": {
                                    "derived": {"is_loop": False},
                                    "features": {"tempo_bpm": 108.0},
                                },
                                "notes": ["preset: mark-fill-as-non-loop"],
                            },
                        }
                    ),
                    normalize_record_schema_v1(
                        {
                            **make_flat_record(
                                file_name="KSHMR_128_drum_fill_long_adrenaline.wav",
                                source_path=str(temp_path / "fill2.wav"),
                            ),
                            "review": {
                                "overrides": {
                                    "derived": {"is_loop": False, "tempo_applicable": False},
                                    "features": {"tempo_quality": "not_applicable"},
                                },
                                "notes": ["batch b2: restore BPM from filename"],
                            },
                        }
                    ),
                    normalize_record_schema_v1(
                        {
                            **make_flat_record(
                                file_name="KSHMR_crash_acoustic_dark.wav",
                                source_path=str(temp_path / "dark.wav"),
                            ),
                            "review": {
                                "overrides": {
                                    "derived": {"brightness": "dark"},
                                },
                                "notes": ["preset: mark-dark-name-as-dark"],
                            },
                        }
                    ),
                ],
            }
            input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = app.main(
                    [
                        "review-stats",
                        "--input",
                        str(input_path),
                        "--top-notes",
                        "5",
                        "--top-combos",
                        "5",
                        "--top-keywords",
                        "5",
                    ]
                )

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Reviewed records: 3", output)
            self.assertIn("derived.is_loop: 2", output)
            self.assertIn("derived.brightness: 1", output)
            self.assertIn("derived.tempo_applicable: 1", output)
            self.assertIn("features.tempo_bpm: 1", output)
            self.assertIn("features.tempo_quality: 1", output)
            self.assertIn("Most common note prefixes:", output)
            self.assertIn("preset: 2", output)
            self.assertIn("batch b2: 1", output)
            self.assertIn("Inferred correction sources:", output)
            self.assertIn("mark-fill-as-non-loop: 1", output)
            self.assertIn("mark-dark-name-as-dark: 1", output)
            self.assertIn("restore-bpm-from-filename-for-loops: 1", output)
            self.assertIn("fill", output)
            self.assertIn("dark", output)


if __name__ == "__main__":
    unittest.main()
