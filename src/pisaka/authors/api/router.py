from typing import Annotated

from aioinject import Inject
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pisaka.authors.ids import AuthorId
from pisaka.authors.models import AuthorModel
from pisaka.platform.api import BaseSchema

router = APIRouter(
    prefix="/authors",
    tags=["Авторы"],
)


class AuthorSchema(BaseSchema):
    id: AuthorId
    name: str


class AuthorsListSchema(BaseSchema):
    authors: list[AuthorSchema]


@router.get(path="/")
@inject
async def get_authors_list(
    session: Annotated[AsyncSession, Inject],
) -> AuthorsListSchema:
    result = await session.execute(select(AuthorModel))
    return AuthorsListSchema(
        authors=[
            AuthorSchema.model_validate(author) for author in result.scalars().all()
        ],
    )


@router.get(path="/{author_id}")
@inject
async def get_author(
    author_id: Annotated[AuthorId, Path(description="ID автора")],
    session: Annotated[AsyncSession, Inject],
) -> AuthorSchema:
    result = await session.execute(
        select(AuthorModel).where(AuthorModel.id == author_id),
    )
    return AuthorSchema.model_validate(result.scalar_one())
