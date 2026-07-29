from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # OpenAI — LLM (conversa) e STT (transcrição de voz)
    openai_api_key: str
    openai_model: str = "gpt-5.6-luna"
    stt_model: str = "gpt-4o-transcribe"

    # ElevenLabs — TTS (síntese de voz)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    elevenlabs_model: str = "eleven_multilingual_v2"  # suporta português

    # Aplicação
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "vivia.db"
    port: int = 8000


settings = Settings()