"""OPTIONAL: audio -> text via Groq Whisper. The UI always shows the transcript for review before summarising."""
from backend.config import get_api_key, get_setting
from backend.services.llm_service import map_provider_error
from backend.utils.logging_utils import get_logger, redact
from backend.utils.validators import validate_audio

log = get_logger(__name__)


def audio_available() -> bool:
    return bool(get_api_key("groq"))


def transcribe_audio(filename: str, data: bytes) -> str:
    validate_audio(filename, len(data))
    key = get_api_key("groq")
    if not key:
        from backend.services.llm_service import MissingKeyError

        raise MissingKeyError("Audio transcription needs a Groq API key.")
    try:
        from groq import Groq

        model = get_setting("WHISPER_MODEL", "whisper-large-v3")
        client = Groq(api_key=key, timeout=120)
        result = client.audio.transcriptions.create(file=(filename, data), model=model, response_format="text")
        text = result if isinstance(result, str) else getattr(result, "text", "")
    except Exception as exc:
        log.warning("Transcription failed: %s", redact(str(exc))[:200])
        raise map_provider_error(exc) from exc
    if not text.strip():
        raise ValueError("No speech was detected in the audio file.")
    return text.strip()
