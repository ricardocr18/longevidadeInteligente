from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # OpenAI
    openai_api_key: str
    # openai_model: str = "gpt-4o"
    openai_model: str = "gpt-5.6-luna"

    # ElevenLabs (opcionais na Fase 1)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # Aplicação
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "vivia.db"
    port: int = 8000


settings = Settings()