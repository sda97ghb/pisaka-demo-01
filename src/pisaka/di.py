from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass

import aioinject
from starlette.types import ASGIApp


_jwt_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgQCFnu5QVffnlErf8Egsyat0YVMnwE6r8IRmsOxKKrR5yWGiNmSk
AQVG3RbnSMeDQw1PbGrNXC6TAkENRetwFFoG87is0wYxpDovlxhFXa8k92ofoHPI
ofG6S4yFPWU2MdyISPKHxRveLX/Us9CjN4kiv+9Tgu1bRQwAnFl+M6+L3QIDAQAB
AoGANv8JG2um01wHzU/6hOSkewwry6qtNruR4ypitswI6C9ozfkRRydcYqRQ7vTX
mUEZ01zOQKP2T2+YErx6gPD/dFDCBl5of6V59Jcv4IKywT5zu2yrd5zIaZr7M1JO
fbVUeaGkKhXNu0T3ZaIs1q1lsX7XZQh7PvXI7lVg1DXMR4kCQQC+CPJThnDSyly0
2dtJmZNKE6a7RRaiqSHjlR2NVMAjLDjgdrhblzF93KotzSggylh/X7t6yaOsg4gN
ooHrgBhPAkEAtADc1LxNhrr9JObH5bN5e8mYOr3KzaW7i9B4vNJMJgPRitxQPPiV
Mx01tR7c1wpr/HxZHDM2Dtz5aw6WesjiEwJAGkeUc1aJLa1Maroh6CizxK+5A/bG
7ZGkHRvW7V+F/pcz+l6QmiHrdzNX2WOgpAA3gs3TWGSgHNBHtVL+0nlxYwJAMuqT
jLF/FH9MH+YP4U+1K2jI4MTS2vzoYhIkNPUfiRlHaooLQFPokD7Q9Fy4hzNxfEgI
RMvPnMCw5LGJq02rdQJAF3DtS4duwmAskabrpN/6k3ENum5gtTcgbod/whBZQalB
IZdSlzTGyNIYSnbhXjOeliGB1A5oVmBBOczW2koxRg==
-----END RSA PRIVATE KEY-----"""

_jwt_public_key = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCFnu5QVffnlErf8Egsyat0YVMn
wE6r8IRmsOxKKrR5yWGiNmSkAQVG3RbnSMeDQw1PbGrNXC6TAkENRetwFFoG87is
0wYxpDovlxhFXa8k92ofoHPIofG6S4yFPWU2MdyISPKHxRveLX/Us9CjN4kiv+9T
gu1bRQwAnFl+M6+L3QIDAQAB
-----END PUBLIC KEY-----"""


@dataclass
class Config:
    db_url_sync: str
    db_url_async: str
    db_echo: bool
    jwt_private_key: str
    jwt_public_key: str
    jwt_audience: str
    jwt_issuer: str
    jwt_algorithm: str
    jwt_leeway_sec: int


def _create_di_container() -> aioinject.Container:
    container = aioinject.Container()
    container.register(aioinject.Object(container, aioinject.Container))
    container.register(
        aioinject.Object(
            Config(
                db_url_sync="sqlite:///db.sqlite",
                db_url_async="sqlite+aiosqlite:///db.sqlite",
                db_echo=True,
                jwt_private_key=_jwt_private_key,
                jwt_public_key=_jwt_public_key,
                jwt_audience="pisaka-backend",
                jwt_issuer="https://my-sso-instance/realm/our-dudes",
                jwt_algorithm="RS256",
                jwt_leeway_sec=60,
            ),
        ),
    )
    _register_db(container)
    _register_authors(container)
    return container


def _register_db(container: aioinject.Container) -> None:
    from sqlalchemy import Engine, create_engine
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
    from sqlalchemy.orm import Session

    @contextmanager
    def _create_engine(config: Config) -> Iterator[Engine]:
        engine = create_engine(url=config.db_url_sync, echo=config.db_echo)
        yield engine
        engine.dispose()

    @asynccontextmanager
    async def _create_async_engine(config: Config) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(url=config.db_url_async, echo=config.db_echo)
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
    from pisaka.authors import (
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
    from pisaka.api import create_app

    container = _create_di_container()
    return create_app(container=container)


def internal_api_app() -> ASGIApp:
    from pisaka.internal_api import create_app
    from pisaka.internal_api.authentication import JWTAuthentication, JWTAuthenticationOptions

    def _create_jwt_authentication_options(config: Config) -> JWTAuthenticationOptions:
        return JWTAuthenticationOptions(
            public_key=config.jwt_public_key,
            audience=config.jwt_audience,
            issuer=config.jwt_issuer,
            algorithm=config.jwt_algorithm,
            leeway_sec=config.jwt_leeway_sec,
        )

    container = _create_di_container()
    container.register(aioinject.Singleton(_create_jwt_authentication_options))
    container.register(aioinject.Scoped(JWTAuthentication))
    return create_app(container=container)


def init_db() -> None:
    from sqlalchemy import Engine

    import pisaka.db

    container = _create_di_container()
    with container.sync_context() as ctx:
        engine: Engine = ctx.resolve(Engine)
        pisaka.db.DBModel.metadata.create_all(bind=engine)


def create_jwt_token() -> None:
    import jwt
    from uuid import uuid4
    from datetime import datetime, timedelta

    container = _create_di_container()
    with container.sync_context() as ctx:
        config = ctx.resolve(Config)
        user_id = str(uuid4())
        now = datetime.now()

        encoded: str = jwt.encode(
            payload={
                "jti": str(uuid4()),
                "iss": config.jwt_issuer,
                "sub": user_id,
                "iat": now.timestamp(),
                "nbf": now.timestamp(),
                "exp": (now + timedelta(minutes=30)).timestamp(),
                "aud": [config.jwt_audience],
                "azp": "pisaka-frontend",
                "username": "j.doe",
                "email": "j.doe@mail.com",
                "given_name": "John",
                "family_name": "Doe",
            },
            key=config.jwt_private_key,
            algorithm=config.jwt_algorithm,
        )
        print(encoded)


if __name__ == "__main__":
    import sys
    match sys.argv[1]:
        case "init_db":
            init_db()
        case "jwt":
            create_jwt_token()
        case _:
            print("Unknown command")
