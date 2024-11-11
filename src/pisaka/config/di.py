from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

import aioinject
from starlette.types import ASGIApp

from pisaka.config.config_files import Config, load_config, load_raw_config
from pisaka.platform.logging import init_logging


def _create_di_container(config: Config) -> aioinject.Container:
    container = aioinject.Container()
    container.register(aioinject.Object(container, aioinject.Container))
    container.register(aioinject.Object(config))
    _register_db(container)
    _register_authors(container)
    return container


def _register_db(container: aioinject.Container) -> None:
    from sqlalchemy import Engine, create_engine
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
    from sqlalchemy.orm import Session

    @contextmanager
    def _create_engine(config: Config) -> Iterator[Engine]:
        engine = create_engine(url=config.db.url_sync)
        yield engine
        engine.dispose()

    @asynccontextmanager
    async def _create_async_engine(config: Config) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(url=config.db.url_async)
        yield engine
        await engine.dispose()

    @contextmanager
    def _create_session(engine: Engine) -> Iterator[Session]:
        with Session(bind=engine, expire_on_commit=False) as session:
            yield session

    @asynccontextmanager
    async def _create_async_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
        async with AsyncSession(bind=engine, expire_on_commit=False) as session:
            yield session

    container.register(aioinject.Singleton(_create_engine))
    container.register(aioinject.Singleton(_create_async_engine))
    container.register(aioinject.Scoped(_create_session))
    container.register(aioinject.Scoped(_create_async_session))


def _register_authors(container: aioinject.Container) -> None:
    from pisaka.app.authors import (
        AuthorRepository,
        CreateAuthorCommand,
        DefaultAuthorService,
        DeleteAuthorCommand,
        ResetDefaultAuthorCommand,
        SetDefaultAuthorCommand,
        UpdateAuthorCommand,
    )

    container.register(aioinject.Scoped(AuthorRepository))
    container.register(aioinject.Scoped(CreateAuthorCommand))
    container.register(aioinject.Scoped(UpdateAuthorCommand))
    container.register(aioinject.Scoped(DeleteAuthorCommand))
    container.register(aioinject.Scoped(DefaultAuthorService))
    container.register(aioinject.Scoped(SetDefaultAuthorCommand))
    container.register(aioinject.Scoped(ResetDefaultAuthorCommand))


def public_api_app() -> ASGIApp:
    from pisaka.app.api import create_app
    from pisaka.platform.security.authentication.common import JWTAuthenticationOptions

    config = load_config()

    init_logging(config.logging)

    def _create_jwt_authentication_options(config: Config) -> JWTAuthenticationOptions:
        return JWTAuthenticationOptions(
            public_key=config.api.jwt_authentication.public_key,
            audience=config.api.jwt_authentication.audience,
            issuer=config.api.jwt_authentication.issuer,
            algorithm=config.api.jwt_authentication.algorithm,
            leeway_sec=config.api.jwt_authentication.leeway_sec,
        )

    container = _create_di_container(config=config)
    container.register(aioinject.Singleton(_create_jwt_authentication_options))
    return create_app(container=container)


def internal_api_app() -> ASGIApp:
    from pisaka.app.internal_api import create_app
    from pisaka.platform.security.authentication.common import JWTAuthenticationOptions

    config = load_config()

    init_logging(config.logging)

    def _create_jwt_authentication_options(config: Config) -> JWTAuthenticationOptions:
        return JWTAuthenticationOptions(
            public_key=config.internal_api.jwt_authentication.public_key,
            audience=config.internal_api.jwt_authentication.audience,
            issuer=config.internal_api.jwt_authentication.issuer,
            algorithm=config.internal_api.jwt_authentication.algorithm,
            leeway_sec=config.internal_api.jwt_authentication.leeway_sec,
        )

    container = _create_di_container(config=config)
    container.register(aioinject.Singleton(_create_jwt_authentication_options))
    return create_app(container=container)


def init_db() -> None:
    from sqlalchemy import Engine

    import pisaka.platform.db

    config = load_config()

    container = _create_di_container(config=config)
    with container.sync_context() as ctx:
        engine: Engine = ctx.resolve(Engine)
        pisaka.platform.db.DBModel.metadata.create_all(bind=engine)


def create_jwt_token() -> None:
    from datetime import datetime, timedelta
    from uuid import uuid4

    import jwt

    config = load_config()

    container = _create_di_container(config=config)
    with container.sync_context() as ctx:
        config = ctx.resolve(Config)
        user_id = str(uuid4())
        now = datetime.now()  # noqa: DTZ005

        encoded: str = jwt.encode(
            payload={
                "jti": str(uuid4()),
                "iss": config.internal_api.jwt_authentication.issuer,
                "sub": user_id,
                "iat": now.timestamp(),
                "nbf": now.timestamp(),
                "exp": (now + timedelta(minutes=30)).timestamp(),
                "aud": [config.internal_api.jwt_authentication.audience],
                "azp": "pisaka-frontend",
                "username": "j.doe",
                "email": "j.doe@mail.com",
                "given_name": "John",
                "family_name": "Doe",
            },
            key=config.internal_api.jwt_authentication.private_key,
            algorithm=config.internal_api.jwt_authentication.algorithm,
        )
        print(encoded)  # noqa: T201


def print_config() -> None:
    import sys
    from pprint import pprint

    if len(sys.argv) >= 3 and sys.argv[2] == "--raw":  # noqa: PLR2004
        raw_config = load_raw_config()
        pprint(dict(raw_config))  # noqa: T203
        return

    config = load_config()
    print(config.model_dump_json(indent=2))  # noqa: T201


def test_logging() -> None:
    import logging

    config = load_config()
    init_logging(config.logging)
    log = logging.getLogger("my.foo")
    log.info("Msg with info")
    log.warning("Achtung! %d", 13)


if __name__ == "__main__":
    import sys

    match sys.argv[1]:
        case "init_db":
            init_db()
        case "jwt":
            create_jwt_token()
        case "config":
            print_config()
        case "log":
            test_logging()
        case _:
            print("Unknown command")  # noqa: T201
