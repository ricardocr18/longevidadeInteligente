from elevenlabs.client import ElevenLabs
from vivia.config import settings

_client: ElevenLabs | None = None


def _get_client() -> ElevenLabs:
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    return _client


def synthesize_speech(text: str) -> bytes:
    """
    Converte texto em áudio (MP3) usando a ElevenLabs.
    Retorna os bytes do áudio prontos para tocar no navegador.
    """
    client = _get_client()

    audio_stream = client.text_to_speech.convert(
        text=text,
        voice_id=settings.elevenlabs_voice_id,
        model_id=settings.elevenlabs_model,
    )
    return b"".join(audio_stream)