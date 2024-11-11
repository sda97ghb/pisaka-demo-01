from dynaconf import Dynaconf  # type:ignore[import-untyped]
from pydantic import BaseModel, ConfigDict

from pisaka.platform.logging import LoggingConfig


class DB(BaseModel):
    url_sync: str
    url_async: str


class JWT(BaseModel):
    private_key: str
    public_key: str
    audience: str
    issuer: str
    algorithm: str
    leeway_sec: int


class API(BaseModel):
    jwt_authentication: JWT


class InternalAPI(BaseModel):
    jwt_authentication: JWT


class Config(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    logging: LoggingConfig
    db: DB
    api: API
    internal_api: InternalAPI


def load_raw_config() -> Dynaconf:
    return Dynaconf(
        core_loaders=["YAML", "TOML", "JSON"],
        load_dotenv=True,
        envvar_prefix="PISAKA",
    )


def load_config() -> Config:
    return Config.model_validate(load_raw_config())
