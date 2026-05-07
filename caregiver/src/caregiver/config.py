"""Application settings and configuration."""

import re
import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, computed_field

class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_URL : str = "http://localhost:8000"

    GOOGLE_JSON_SECRET : SecretStr = SecretStr("secret")
    GOOGLE_CLIENT_ID : str = "google_client_id"
    GOOGLE_CLIENT_SECRET : SecretStr = SecretStr("google_client_secret")

    @computed_field
    @property
    def GOOGLE_JSON(self) -> dict:
        google_secrent_parsed = re.sub(r'(?<!\\)\n', '', self.GOOGLE_JSON_SECRET.get_secret_value())
        return json.loads(google_secrent_parsed)

    GOOGLE_SHEET_ID : str = "google_sheet_id"

    ALLOWED_EMAILS_STR : str = ""
    @computed_field
    @property
    def ALLOWED_EMAILS(self) -> list[str]:
        return [email.strip() for email in self.ALLOWED_EMAILS_STR.split(",") if email.strip()]
