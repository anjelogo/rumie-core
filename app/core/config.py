from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    mongo_uri: str = "mongodb://mongodb:27017/?replicaSet=rs0"
    mongo_db: str = "rumie"

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minio_root"
    minio_secret_key: str = "change_me_minimum_8_chars"
    minio_bucket: str = "assets"
    minio_secure: bool = False

    public_asset_base: str = "https://rumie.xyz/assets"

    jwt_secret: str = "dev_only_change_me"
    jwt_alg: str = "HS256"
    access_ttl_s: int = 900
    refresh_ttl_s: int = 2592000
    presign_ttl_s: int = 900


settings = Settings()
