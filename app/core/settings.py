from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import EnvType

# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------


class AppSettings(BaseSettings):
    # Pydantic automatically converts ENV_VAR to lowercase setting_name
    enabled_cron: bool = False
    environment: EnvType = EnvType.DEVELOPMENT

    app_name: str = "TemplateBot"
    app_version: str = "2025.01.15"
    database_path: str = "sqlite:///data/development.db"

    log_file: str = "development.log"
    log_level: str = "INFO"

    notifier_discord_webhook_url: str = ""
    notifier_telegram_token: str = ""
    notifier_telegram_chat_id: str = ""

    # 'model_config' is a reserved and required name that Pydantic V2
    # uses internally to find and interpret the configuration dictionary
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # normalize log_level
    @field_validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate and normalize the log level."""
        if isinstance(v, str):
            v = v.strip().upper()
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            print("\nInvalid log level specified")
            return "INFO"
        return v


settings = AppSettings()
