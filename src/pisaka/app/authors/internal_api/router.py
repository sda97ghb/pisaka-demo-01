from typing import Annotated
from uuid import UUID

from aioinject import Inject
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Body, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pisaka.app.authors.commands import (
    CreateAuthorCommand,
    DeleteAuthorCommand,
    ResetDefaultAuthorCommand,
    SetDefaultAuthorCommand,
    UpdateAuthorCommand,
)
from pisaka.app.authors.ids import AuthorId
from pisaka.app.authors.models import AuthorModel
from pisaka.app.authors.services import DefaultAuthorService
from pisaka.platform.api import BaseSchema
from pisaka.platform.security.authentication.internal_api import Authentication

router = APIRouter(
    prefix="/authors",
    tags=["Авторы"],
)


class AuthorSchema(BaseSchema):
    id: AuthorId
    name: str
    is_real_person: bool


class AuthorsListSchema(BaseSchema):
    authors: list[AuthorSchema]


@router.get(path="/")
@inject
async def get_authors_list(
    session: Annotated[AsyncSession, Inject],
    authentication: Authentication,
) -> AuthorsListSchema:
    print("Principal:", authentication.principal)  # noqa: T201
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


class CreateAuthorResponseSchema(BaseSchema):
    author: AuthorSchema


@router.post(path="/")
@inject
async def create_author(
    name: Annotated[str, Body(embed=True)],
    is_real_person: Annotated[bool, Body(embed=True)],
    create_author_command: Annotated[CreateAuthorCommand, Inject],
) -> CreateAuthorResponseSchema:
    author = await create_author_command.execute(
        name=name,
        is_real_person=is_real_person,
    )
    return CreateAuthorResponseSchema(author=AuthorSchema.model_validate(author))


class UpdateAuthorResponseSchema(BaseSchema):
    author: AuthorSchema


@router.put(path="/{author_id}")
@inject
async def update_author(
    author_id: Annotated[AuthorId, Path(description="ID автора")],
    name: Annotated[str, Body(embed=True)],
    update_author_command: Annotated[UpdateAuthorCommand, Inject],
) -> UpdateAuthorResponseSchema:
    author = await update_author_command.execute(author_id=author_id, new_name=name)
    return UpdateAuthorResponseSchema(author=AuthorSchema.model_validate(author))


@router.delete(path="/{author_id}")
@inject
async def delete_author(
    author_id: Annotated[AuthorId, Path(description="ID автора")],
    delete_author_command: Annotated[DeleteAuthorCommand, Inject],
) -> None:
    await delete_author_command.execute(author_id=author_id)


class DefaultAuthorSchema(BaseSchema):
    user_id: UUID
    author_id: AuthorId


class DefaultAuthorsListSchema(BaseSchema):
    items: list[DefaultAuthorSchema]


@router.get(path="/default")
@inject
async def get_all_default_authors(
    default_author_service: Annotated[DefaultAuthorService, Inject],
) -> DefaultAuthorsListSchema:
    defaults_authors = await default_author_service.get_all()
    return DefaultAuthorsListSchema(
        items=[
            DefaultAuthorSchema.model_validate(default_author)
            for default_author in defaults_authors
        ],
    )


@router.put(path="/default/for-user/{user_id}")
@inject
async def set_default_author(
    user_id: Annotated[UUID, Path()],
    author_id: Annotated[AuthorId, Body(embed=True)],
    set_default_author_command: Annotated[SetDefaultAuthorCommand, Inject],
) -> None:
    await set_default_author_command.execute(user_id=user_id, author_id=author_id)


@router.delete(path="/default/for-user/{user_id}")
@inject
async def reset_default_author(
    user_id: Annotated[UUID, Path()],
    reset_default_author_command: Annotated[ResetDefaultAuthorCommand, Inject],
) -> None:
    await reset_default_author_command.execute(user_id=user_id)
