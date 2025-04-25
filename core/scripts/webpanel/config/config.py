from pydantic_settings import BaseSettings


class Configs(BaseSettings):
    PORT: int
    DOMAIN: str
    DEBUG: bool
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    API_TOKEN: str
    EXPIRATION_MINUTES: int
    ROOT_PATH: str
    DECOY_PATH: str | None = None

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


CONFIGS = Configs()  # type: ignore
