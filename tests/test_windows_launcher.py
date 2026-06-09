from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "start_web_ui.bat"


def test_windows_web_ui_launcher_exists():
    assert LAUNCHER.exists()


def test_windows_web_ui_launcher_mentions_expected_command_and_env_vars():
    script = LAUNCHER.read_text(encoding="utf-8")

    for expected in ["web_server.py", "AMM_LIBRARY", "AMM_SAMPLES", "AMM_PORT"]:
        assert expected in script
