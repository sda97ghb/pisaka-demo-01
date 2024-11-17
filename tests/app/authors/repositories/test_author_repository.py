from collections.abc import AsyncGenerator
from uuid import uuid4

import aioinject
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from pisaka.app.authors import Author, AuthorId, AuthorRepository
from pisaka.config.config_files import load_config
from pisaka.config.di import create_base_di_container
from pisaka.platform.errors import NotFoundError
from pisaka.platform.logging import init_logging

pytestmark = [pytest.mark.anyio]


@pytest.fixture
async def di_container() -> AsyncGenerator[aioinject.Container, None]:
    config = load_config()
    init_logging(config.logging)
    container = create_base_di_container(config)
    async with container:
        yield container


@pytest.fixture
async def ctx(
    di_container: aioinject.Container,
) -> AsyncGenerator[aioinject.InjectionContext, None]:
    async with di_container.context() as ctx:
        yield ctx


async def test_save(ctx: aioinject.InjectionContext) -> None:
    author_id = AuthorId(uuid4())

    repository = await ctx.resolve(AuthorRepository)
    session = await ctx.resolve(AsyncSession)

    await session.begin()
    try:
        author_to_save = Author.create(
            id_=author_id,
            name="J. Doe",
            is_real_person=False,
        )

        await repository.save(author_to_save)

        session.expunge_all()

        saved_author = await repository.get(author_id=author_id)

        assert saved_author.id == author_id
        assert saved_author.name == author_to_save.name
        assert saved_author.is_real_person == author_to_save.is_real_person
    finally:
        await session.rollback()


async def test_get__not_found(ctx: aioinject.InjectionContext) -> None:
    non_existent_author_id = AuthorId(uuid4())
    repository = await ctx.resolve(AuthorRepository)
    with pytest.raises(NotFoundError):
        await repository.get(author_id=non_existent_author_id)


async def test_delete(ctx: aioinject.InjectionContext) -> None:
    author_id = AuthorId(uuid4())

    repository = await ctx.resolve(AuthorRepository)
    session = await ctx.resolve(AsyncSession)

    await session.begin()
    try:
        author_to_save = Author.create(
            id_=author_id,
            name="J. Doe",
            is_real_person=False,
        )

        await repository.save(author_to_save)

        session.expunge_all()

        await repository.get(author_id=author_id)

        await repository.delete(author_id=author_id)

        with pytest.raises(NotFoundError):
            await repository.get(author_id=author_id)
    finally:
        await session.rollback()
