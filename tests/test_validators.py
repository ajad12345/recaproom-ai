import pytest

from backend.utils.validators import validate_audio, validate_text_input, validate_upload

WORDS = " ".join(["word"] * 60)


def test_empty_input_rejected():
    """empty string -> ValueError asking user to paste a transcript"""
    with pytest.raises(ValueError, match="paste or upload"):
        validate_text_input("   ")


def test_too_short_rejected():
    """5-word transcript -> ValueError (too short)"""
    with pytest.raises(ValueError, match="too short"):
        validate_text_input("only five words in here")


def test_short_but_allowed_warns():
    """30-word transcript -> accepted with a 'very short' warning"""
    text, warns = validate_text_input(" ".join(["alpha"] * 30))
    assert warns and "short" in warns[0].lower()


def test_gibberish_rejected():
    """symbols/digits only -> ValueError (not readable text)"""
    with pytest.raises(ValueError, match="readable"):
        validate_text_input(" ".join(["1234567890!!"] * 40))


def test_too_long_rejected():
    """61,000-word text -> ValueError with split advice"""
    with pytest.raises(ValueError, match="too long"):
        validate_text_input(" ".join(["word"] * 61_000))


def test_valid_text_ok():
    """60-word transcript -> accepted without warnings"""
    text, warns = validate_text_input(WORDS)
    assert text and warns == []


def test_wrong_extension_rejected():
    """notes.pdf upload -> ValueError (only .txt)"""
    with pytest.raises(ValueError, match="Unsupported file type"):
        validate_upload("notes.pdf", b"hello")


def test_empty_file_rejected():
    """0-byte .txt upload -> ValueError (empty file)"""
    with pytest.raises(ValueError, match="empty"):
        validate_upload("a.txt", b"")


def test_oversized_file_rejected():
    """3 MB .txt upload -> ValueError (too large)"""
    with pytest.raises(ValueError, match="too large"):
        validate_upload("a.txt", b"a " * (1_600_000))


def test_binary_file_rejected():
    """.txt containing NUL bytes -> ValueError (binary)"""
    with pytest.raises(ValueError, match="binary"):
        validate_upload("a.txt", b"\x00\x01\x02" * 100)


def test_latin1_fallback():
    """latin-1 encoded .txt -> decoded successfully"""
    data = ("caf\xe9 " * 40).encode("latin-1")
    text, _ = validate_upload("a.txt", data)
    assert "caf" in text


def test_audio_validation():
    """.ogg audio -> ValueError; .mp3 within limit -> accepted"""
    with pytest.raises(ValueError):
        validate_audio("a.ogg", 100)
    validate_audio("a.mp3", 100)
