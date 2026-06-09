from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "development" / "amm-architecture-roadmap.md"


def test_architecture_roadmap_covers_target_layers_and_desktop_direction():
    text = ROADMAP.read_text(encoding="utf-8")

    for phrase in [
        "audio_metadata.library",
        "Core library",
        "CLI",
        "Client",
        "Tauri",
        "Electron",
        "amm_config.json",
    ]:
        assert phrase in text
