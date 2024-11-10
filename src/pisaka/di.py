from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass

import aioinject
from starlette.types import ASGIApp


@dataclass
class Config:
    db_url_sync: str
    db_url_async: str
    db_echo: bool


def _create_di_container() -> aioinject.Container:
    container = aioinject.Container()
    container.register(aioinject.Object(container, aioinject.Container))
    container.register(
        aioinject.Object(
            Config(
                db_url_sync="sqlite:///db.sqlite",
                db_url_async="sqlite+aiosqlite:///db.sqlite",
                db_echo=True,
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

    container = _create_di_container()
    return create_app(container=container)


def init_db() -> None:
    from sqlalchemy import Engine

    import pisaka.db

    container = _create_di_container()
    with container.sync_context() as ctx:
        engine: Engine = ctx.resolve(Engine)
        pisaka.db.DBModel.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
