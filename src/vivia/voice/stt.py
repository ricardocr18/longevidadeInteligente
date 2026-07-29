from openai import OpenAI
from vivia.config import settings


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Transcreve áudio para texto usando o modelo de transcrição da OpenAI.

    audio_bytes: conteúdo bruto do arquivo de áudio (webm, mp3, wav, m4a — o
    formato que o navegador gravar). A extensão em `filename` importa: é
    como a API identifica o formato do arquivo.
    """
    client = OpenAI(api_key=settings.openai_api_key)

    transcript = client.audio.transcriptions.create(
        model=settings.stt_model,
        file=(filename, audio_bytes),
        language="pt",
    )
    return transcript.text