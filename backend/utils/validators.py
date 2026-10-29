"""Input and file validation. Every failure raises ValueError with a user-readable message."""
from pathlib import Path

MAX_FILE_BYTES = 2 * 1024 * 1024
MIN_WORDS = 20
SHORT_WORDS_WARN = 50
SOFT_MAX_WORDS = 20_000
HARD_MAX_WORDS = 60_000
ALLOWED_EXT = {".txt"}
ALLOWED_AUDIO_EXT = {".mp3", ".wav", ".m4a"}
MAX_AUDIO_BYTES = 24 * 1024 * 1024


def count_words(text: str) -> int:
    return len((text or "").split())


def validate_text_input(text) -> tuple[str, list[str]]:
    """Return (cleaned_text, warnings). Raise ValueError if the text can't be processed."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Please paste or upload a transcript first.")
    words = count_words(text)
    if words < MIN_WORDS:
        raise ValueError(f"The transcript is too short ({words} words). Please provide at least {MIN_WORDS} words.")
    if words > HARD_MAX_WORDS:
        raise ValueError(
            f"The transcript is too long ({words:,} words). The limit is {HARD_MAX_WORDS:,} words. "
            "Please split it into parts and summarise each one."
        )
    visible = [c for c in text if not c.isspace()]
    letters = sum(c.isalpha() for c in visible)
    if not visible or letters / len(visible) < 0.5:
        raise ValueError("This doesn't look like readable text. Please check the transcript.")
    warnings: list[str] = []
    if words < SHORT_WORDS_WARN:
        warnings.append("Very short transcript: the notes may be thin.")
    if words > SOFT_MAX_WORDS:
        warnings.append("Very long transcript: this may take several minutes and may hit provider rate limits.")
    return text, warnings


def decode_bytes(data: bytes) -> str:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("The file could not be decoded as text.")


def validate_upload(filename: str, data: bytes) -> tuple[str, list[str]]:
    """Validate an uploaded .txt file and return (text, warnings)."""
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise ValueError(f"Unsupported file type '{ext or 'unknown'}'. Please upload a .txt file.")
    if not data:
        raise ValueError("The uploaded file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"The file is too large ({len(data) / 1_048_576:.1f} MB). The limit is 2 MB.")
    if b"\x00" in data[:4096]:
        raise ValueError("This looks like a binary file, not a text transcript.")
    return validate_text_input(decode_bytes(data))


def validate_audio(filename: str, size: int) -> None:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_AUDIO_EXT:
        raise ValueError("Unsupported audio type. Please upload an mp3, wav or m4a file.")
    if size <= 0:
        raise ValueError("The audio file is empty.")
    if size > MAX_AUDIO_BYTES:
        raise ValueError("The audio file is too large (limit 24 MB).")
