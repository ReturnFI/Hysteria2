from pydantic_settings import BaseSettings


class Configs(BaseSettings):
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    API_TOKEN: str
    EXPIRATION_MINUTES: int
    DEBUG: bool

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


CONFIGS = Configs()  # type: ignore
