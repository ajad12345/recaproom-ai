"""Helpers for the bundled synthetic sample transcripts."""
from pathlib import Path

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "data" / "sample"


def list_samples() -> list[str]:
    return sorted(p.name for p in SAMPLE_DIR.glob("*.txt"))


def read_sample(name: str) -> str:
    path = SAMPLE_DIR / Path(name).name  # strip any directory parts
    return path.read_text(encoding="utf-8") if path.exists() else ""
