from __future__ import annotations

import io
import json
import shutil
import sys
import unittest
import uuid
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import review_metadata
import search_metadata
import search_similar
from audio_metadata.schema import normalize_payload_schema_v1, normalize_record_schema_v1


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


class SchemaOverrideTests(unittest.TestCase):
    def test_normalize_record_applies_valid_review_overrides_and_sanitizes_invalid_entries(self) -> None:
        record = {
            "status": "ok",
            "source": {
                "path": "C:\\audio\\kick.wav",
                "file_name": "kick.wav",
                "file_format": "wav",
            },
            "technical": {
                "duration_sec": 2.0,
                "sample_rate_hz": 44100,
                "channels": 1,
            },
            "features": {
                "tempo_bpm": 98.0,
                "tempo_quality": "low",
            },
            "derived": {
                "is_loop": True,
                "brightness": "bright",
                "tempo_applicable": True,
            },
            "review": {
                "overrides": {
                    "derived": {
                        "is_loop": False,
                        "brightness": "dark",
                        "tempo_applicable": "invalid",
                        "unknown_field": True,
                    },
                    "features": {
                        "tempo_bpm": None,
                        "tempo_quality": "not_applicable",
                        "spectral_centroid_hz": 9999,
                    },
                },
                "notes": ["manual correction", 3],
                "extra": "keep",
            },
        }

        normalized = normalize_record_schema_v1(record)

        self.assertFalse(normalized["derived"]["is_loop"])
        self.assertEqual(normalized["derived"]["brightness"], "dark")
        self.assertTrue(normalized["derived"]["tempo_applicable"])
        self.assertIsNone(normalized["features"]["tempo_bpm"])
        self.assertEqual(normalized["features"]["tempo_quality"], "not_applicable")
        self.assertFalse(normalized["is_loop"])
        self.assertEqual(normalized["brightness"], "dark")
        self.assertTrue(normalized["tempo_applicable"])
        self.assertIsNone(normalized["review"]["overrides"]["features"]["tempo_bpm"])
        self.assertEqual(normalized["review"]["notes"], ["manual correction"])
        self.assertEqual(normalized["review"]["extra"], "keep")
        self.assertNotIn("tempo_applicable", normalized["review"]["overrides"]["derived"])
        self.assertNotIn("spectral_centroid_hz", normalized["review"]["overrides"]["features"])

    def test_normalize_payload_upgrades_flat_records_to_v1(self) -> None:
        payload = {
            "run": {"generated_at": "2026-03-22T00:00:00+00:00"},
            "files": [
                make_flat_record(
                    file_name="old.wav",
                    source_path="C:\\audio\\old.wav",
                )
            ],
        }

        normalized = normalize_payload_schema_v1(payload)
        record = normalized["files"][0]

        self.assertEqual(normalized["schema_version"], "v1")
        self.assertIn("source", record)
        self.assertIn("derived", record)
        self.assertIn("review", record)
        self.assertEqual(record["source"]["file_name"], "old.wav")
        self.assertTrue(record["derived"]["is_loop"])
        self.assertEqual(record["file_name"], "old.wav")


class ReviewCommandTests(unittest.TestCase):
    def test_review_command_updates_record_and_upgrades_payload(self) -> None:
        with workspace_tempdir() as temp_path:
            source_path = str(temp_path / "target.wav")
            payload_path = temp_path / "library.json"
            payload = {
                "run": {"generated_at": "2026-03-22T00:00:00+00:00"},
                "files": [
                    make_flat_record(file_name="target.wav", source_path=source_path),
                    make_flat_record(file_name="other.wav", source_path=str(temp_path / "other.wav")),
                ],
            }
            payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = review_metadata.main(
                    [
                        "--input",
                        str(payload_path),
                        "--source-path",
                        source_path,
                        "--is-loop",
                        "false",
                        "--brightness",
                        "dark",
                        "--tempo-applicable",
                        "false",
                        "--tempo-bpm",
                        "null",
                        "--tempo-quality",
                        "not_applicable",
                        "--note",
                        "manual correction",
                    ]
                )

            self.assertEqual(exit_code, 0)
            saved_payload = json.loads(payload_path.read_text(encoding="utf-8-sig"))
            target_record = next(record for record in saved_payload["files"] if record["file_name"] == "target.wav")

            self.assertEqual(saved_payload["schema_version"], "v1")
            self.assertEqual(saved_payload["app_version"], "v0.1-b3")
            self.assertEqual(target_record["review"]["notes"], ["manual correction"])
            self.assertEqual(
                target_record["review"]["overrides"],
                {
                    "derived": {
                        "is_loop": False,
                        "brightness": "dark",
                        "tempo_applicable": False,
                    },
                    "features": {
                        "tempo_bpm": None,
                        "tempo_quality": "not_applicable",
                    },
                },
            )
            self.assertFalse(target_record["derived"]["is_loop"])
            self.assertEqual(target_record["derived"]["brightness"], "dark")
            self.assertFalse(target_record["derived"]["tempo_applicable"])
            self.assertIsNone(target_record["features"]["tempo_bpm"])
            self.assertEqual(target_record["features"]["tempo_quality"], "not_applicable")
            self.assertIn("Updated review for target.wav", stdout.getvalue())

    def test_review_command_writes_to_output_and_clears_fields(self) -> None:
        with workspace_tempdir() as temp_path:
            source_path = str(temp_path / "target.wav")
            record = normalize_record_schema_v1(
                {
                    **make_flat_record(file_name="target.wav", source_path=source_path),
                    "review": {
                        "overrides": {
                            "derived": {"is_loop": False},
                            "features": {"tempo_bpm": 128.0, "tempo_quality": "high"},
                        },
                        "notes": ["old note"],
                    },
                }
            )
            payload = {
                "schema_version": "v1",
                "app_version": "v0.1-a",
                "run": {"generated_at": "2026-03-22T00:00:00+00:00"},
                "files": [record],
            }
            input_path = temp_path / "input.json"
            output_path = temp_path / "output.json"
            input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            exit_code = review_metadata.main(
                [
                    "--input",
                    str(input_path),
                    "--id",
                    record["id"],
                    "--output",
                    str(output_path),
                    "--clear",
                    "tempo_bpm",
                    "notes",
                ]
            )

            self.assertEqual(exit_code, 0)
            original_payload = json.loads(input_path.read_text(encoding="utf-8-sig"))
            saved_payload = json.loads(output_path.read_text(encoding="utf-8-sig"))
            saved_record = saved_payload["files"][0]

            self.assertIn("notes", original_payload["files"][0]["review"])
            self.assertNotIn("notes", saved_record["review"])
            self.assertNotIn("tempo_bpm", saved_record["review"]["overrides"]["features"])
            self.assertEqual(saved_record["review"]["overrides"]["features"]["tempo_quality"], "high")

    def test_review_command_rejects_invalid_combinations_and_match_errors(self) -> None:
        with workspace_tempdir() as temp_path:
            source_path = str(temp_path / "target.wav")
            record = normalize_record_schema_v1(make_flat_record(file_name="target.wav", source_path=source_path))
            payload_path = temp_path / "library.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "schema_version": "v1",
                        "app_version": "v0.1-a",
                        "run": {},
                        "files": [record],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            cases = [
                [
                    "--input",
                    str(payload_path),
                    "--id",
                    record["id"],
                ],
                [
                    "--input",
                    str(payload_path),
                    "--id",
                    record["id"],
                    "--is-loop",
                    "false",
                    "--clear",
                    "is_loop",
                ],
                [
                    "--input",
                    str(payload_path),
                    "--id",
                    record["id"],
                    "--source-path",
                    source_path,
                    "--is-loop",
                    "false",
                ],
            ]

            for argv in cases:
                with self.subTest(argv=argv):
                    with self.assertRaises(SystemExit):
                        with redirect_stderr(io.StringIO()):
                            review_metadata.main(argv)

            duplicate_payload_path = temp_path / "duplicates.json"
            duplicate_payload = {
                "schema_version": "v1",
                "app_version": "v0.1-a",
                "run": {},
                "files": [
                    normalize_record_schema_v1(make_flat_record(file_name="a.wav", source_path=source_path)),
                    normalize_record_schema_v1(make_flat_record(file_name="b.wav", source_path=source_path)),
                ],
            }
            duplicate_payload_path.write_text(json.dumps(duplicate_payload, indent=2), encoding="utf-8")

            duplicate_stderr = io.StringIO()
            with redirect_stderr(duplicate_stderr):
                duplicate_exit_code = review_metadata.main(
                    [
                        "--input",
                        str(duplicate_payload_path),
                        "--source-path",
                        source_path,
                        "--is-loop",
                        "false",
                    ]
                )
            self.assertEqual(duplicate_exit_code, 1)
            self.assertIn("More than one record matched", duplicate_stderr.getvalue())

            missing_stderr = io.StringIO()
            with redirect_stderr(missing_stderr):
                missing_exit_code = review_metadata.main(
                    [
                        "--input",
                        str(payload_path),
                        "--source-path",
                        str(temp_path / "missing.wav"),
                        "--is-loop",
                        "false",
                    ]
                )
            self.assertEqual(missing_exit_code, 1)
            self.assertIn("No record matched", missing_stderr.getvalue())


class SearchAndSimilarSmokeTests(unittest.TestCase):
    def test_search_uses_effective_override_values(self) -> None:
        with workspace_tempdir() as temp_path:
            payload_path = temp_path / "library.json"
            payload = {
                "run": {},
                "files": [
                    {
                        **make_flat_record(file_name="target.wav", source_path=str(temp_path / "target.wav")),
                        "review": {
                            "overrides": {
                                "derived": {
                                    "is_loop": False,
                                    "brightness": "dark",
                                    "tempo_applicable": False,
                                },
                                "features": {
                                    "tempo_quality": "not_applicable",
                                },
                            }
                        },
                    },
                    make_flat_record(file_name="other.wav", source_path=str(temp_path / "other.wav")),
                ],
            }
            payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = search_metadata.main(
                    [
                        "--input",
                        str(payload_path),
                        "--is-loop",
                        "false",
                        "--brightness",
                        "dark",
                        "--tempo-applicable",
                        "false",
                        "--tempo-quality",
                        "not_applicable",
                    ]
                )

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Matched 1 record(s).", output)
            self.assertIn("target.wav", output)
            self.assertNotIn("other.wav", output)

    def test_similar_json_input_uses_override_tempo_bpm(self) -> None:
        with workspace_tempdir() as temp_path:
            payload_path = temp_path / "library.json"
            reference_path = temp_path / "reference.wav"
            reference_path.write_bytes(b"placeholder")

            payload = {
                "run": {},
                "files": [
                    {
                        **make_flat_record(file_name="target.wav", source_path=str(temp_path / "target.wav"), tempo_bpm=90.0),
                        "review": {
                            "overrides": {
                                "features": {
                                    "tempo_bpm": 128.0,
                                }
                            }
                        },
                    },
                    make_flat_record(file_name="other.wav", source_path=str(temp_path / "other.wav"), tempo_bpm=100.0),
                ],
            }
            payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            reference_record = normalize_record_schema_v1(
                make_flat_record(
                    file_name="reference.wav",
                    source_path=str(reference_path),
                    tempo_bpm=128.0,
                    tempo_quality="high",
                )
            )

            stdout = io.StringIO()
            with patch("search_similar.build_reference_record", return_value=reference_record):
                with redirect_stdout(stdout):
                    exit_code = search_similar.main(
                        [
                            "--input",
                            str(payload_path),
                            "--reference",
                            str(reference_path),
                            "--min-bpm",
                            "120",
                            "--top-k",
                            "5",
                        ]
                    )

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("filtered_candidates: 1", output)
            self.assertIn("target.wav", output)
            self.assertNotIn("other.wav", output)


if __name__ == "__main__":
    unittest.main()



