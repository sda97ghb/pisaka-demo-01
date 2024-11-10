from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from pisaka.authors.entities import Author
from pisaka.authors.ids import AuthorId
from pisaka.authors.repositories import AuthorRepository
from pisaka.authors.services import DefaultAuthorService


class CreateAuthorCommand:
    def __init__(
        self,
        author_repository: AuthorRepository,
        session: AsyncSession,
    ) -> None:
        self._author_repository = author_repository
        self._session = session

    async def execute(self, *, name: str, is_real_person: bool) -> Author:
        async with self._session.begin():
            author = Author.create(
                id_=AuthorId(uuid4()),
                name=name,
                is_real_person=is_real_person,
            )
            await self._author_repository.save(author)
            return author


class UpdateAuthorCommand:
    def __init__(
        self,
        author_repository: AuthorRepository,
        session: AsyncSession,
    ) -> None:
        self._author_repository = author_repository
        self._session = session

    async def execute(self, author_id: AuthorId, new_name: str) -> Author:
        async with self._session.begin():
            author = await self._author_repository.get(author_id)
            author.set_name(new_name)
            await self._author_repository.save(author)
            return author


class DeleteAuthorCommand:
    def __init__(
        self,
        author_repository: AuthorRepository,
        session: AsyncSession,
    ) -> None:
        self._author_repository = author_repository
        self._session = session

    async def execute(self, author_id: AuthorId) -> None:
        async with self._session.begin():
            await self._author_repository.delete(author_id=author_id)


class SetDefaultAuthorCommand:
    def __init__(
        self,
        default_author_service: DefaultAuthorService,
        session: AsyncSession,
    ) -> None:
        self._default_author_service = default_author_service
        self._session = session

    async def execute(self, user_id: UUID, author_id: AuthorId) -> None:
        async with self._session.begin():
            await self._default_author_service.set(user_id=user_id, author_id=author_id)


class ResetDefaultAuthorCommand:
    def __init__(
        self,
        default_author_service: DefaultAuthorService,
        session: AsyncSession,
    ) -> None:
        self._default_author_service = default_author_service
        self._session = session

    async def execute(self, user_id: UUID) -> None:
        async with self._session.begin():
            await self._default_author_service.reset(user_id=user_id)
