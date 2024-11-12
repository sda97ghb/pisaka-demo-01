from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

import aioinject

from pisaka.config.config_files import Config


def create_base_di_container(config: Config) -> aioinject.Container:
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
