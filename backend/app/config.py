from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "dobrobot"
    debug: bool = False
    secret_key: str = "abcd1234"

    postgres_dsn: str = "postgresql+asyncpg://maxadmin:Admin1234@rc1b-e48029olq8elpa2g.mdb.yandexcloud.net:6432/app"

    redis_url: str = "redis://redis:6379/0"

    allowed_origins: str = "https://max-bot0.vercel.app"

    public_base_url: str = "https://d5df3k4qn0v3e28jf07g.y1haggxy.apigw.yandexcloud.net"

    max_api_base: str = "https://api-max.ru/docs"   
    max_bot_token: str = "BOT_MAX_TOKEN"    
    gateway_stage_prefix: str = ""
             

    class Config:
        env_file = "./.env"
        env_prefix = "BFF_"

settings = Settings()