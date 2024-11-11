from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from pisaka.app.authors.entities import Author
from pisaka.app.authors.ids import AuthorId
from pisaka.app.authors.models import AuthorModel
from pisaka.platform.errors import NotFoundError


class AuthorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id_: AuthorId) -> Author:
        result = await self._session.execute(
            select(AuthorModel).where(AuthorModel.id == id_).with_for_update(),
        )
        model: AuthorModel | None = result.scalar_one_or_none()
        if model is None:
            raise NotFoundError(entity_type=Author, key=id_)
        return Author(model=model)

    async def save(self, author: Author) -> None:
        model = author._model  # noqa: SLF001
        self._session.add(model)
        await self._session.flush([model])

    async def delete(self, author_id: AuthorId) -> None:
        await self._session.execute(
            delete(AuthorModel).where(AuthorModel.id == author_id),
        )
