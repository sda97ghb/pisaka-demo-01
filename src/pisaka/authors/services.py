from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from pisaka.authors.ids import AuthorId
from pisaka.authors.models import DefaultAuthorModel


class DefaultAuthorService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> Sequence[DefaultAuthorModel]:
        result = await self._session.execute(select(DefaultAuthorModel))
        return result.scalars().all()

    async def get(self, user_id: UUID) -> AuthorId | None:
        result = await self._session.execute(
            select(DefaultAuthorModel).where(DefaultAuthorModel.user_id == user_id),
        )
        model: DefaultAuthorModel | None = result.scalar_one_or_none()
        if model is None:
            return None
        return model.author_id

    async def set(self, user_id: UUID, author_id: AuthorId) -> None:
        result_1 = await self._session.execute(
            select(DefaultAuthorModel)
            .where(DefaultAuthorModel.user_id == user_id)
            .with_for_update(),
        )
        model = result_1.scalar_one_or_none()
        if model is None:
            model = DefaultAuthorModel(user_id=user_id, author_id=author_id)
        else:
            model.author_id = author_id
        self._session.add(model)
        await self._session.flush([model])

    async def reset(self, user_id: UUID) -> None:
        await self._session.execute(
            delete(DefaultAuthorModel).where(DefaultAuthorModel.user_id == user_id),
        )
