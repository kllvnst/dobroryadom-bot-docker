from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BOT_",
        env_file=".env",
        case_sensitive=False,
    )

    max_token: str
    bff_base_url: str = "https://d5df3k4qn0v3e28jf07g.y1haggxy.apigw.yandexcloud.net/api/v1"
    public_front_url: str = "https://max-bot0.vercel.app"
    donate_links: str = "https://dobro.mail.ru/sos/"
    city_default: str | None = None
    track_url: str | None = None
    api_alt_paths: str = "/api/v1,/api,/"
    api_alt_urls: str = ""
    classic_flow_enabled: bool = False

settings = Settings()

def donation_list() -> list[str]:
    return [u.strip() for u in settings.donate_links.split(",") if u.strip()]
