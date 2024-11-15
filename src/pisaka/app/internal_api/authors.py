from collections import defaultdict
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from aioinject import Inject
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Body, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from pisaka.app.articles.db import ArticleDraftModel, ArticleModel
from pisaka.app.authors.commands import (
    CreateAuthorCommand,
    DeleteAuthorCommand,
    ResetDefaultAuthorCommand,
    SetDefaultAuthorCommand,
    UpdateAuthorCommand,
)
from pisaka.app.authors.ids import AuthorId
from pisaka.app.authors.models import AuthorModel, DefaultAuthorModel
from pisaka.app.authors.security import EditAuthorsPermission, ListAuthorsPermission
from pisaka.app.authors.services import DefaultAuthorService
from pisaka.platform.api import BaseSchema
from pisaka.platform.security.authentication.internal_api import Authentication
from pisaka.platform.security.authorization import AuthorizationError

router = APIRouter(
    prefix="/authors",
    tags=["Авторы"],
)


class AuthorSchema(BaseSchema):
    id: AuthorId
    name: str
    is_real_person: bool


class AuthorExtendedSchema(AuthorSchema):
    default_for_users: list[UUID]
    count_of_articles: int
    count_of_article_drafts_in_work: int


class AuthorsListSchema(BaseSchema):
    authors: list[AuthorExtendedSchema]


@router.get(path="/")
@inject
async def get_authors_list(
    session: Annotated[AsyncSession, Inject],
    authentication: Authentication,
    list_authors_permission: Annotated[ListAuthorsPermission, Inject],
) -> AuthorsListSchema:
    can_list_authors = await list_authors_permission.evaluate(
        principal=authentication.principal,
    )
    if not can_list_authors:
        raise AuthorizationError

    result_1 = await session.execute(select(AuthorModel))
    authors: Sequence[AuthorModel] = result_1.scalars().all()

    result_2 = await session.execute(select(DefaultAuthorModel))
    default_authors: dict[AuthorId, list[UUID]] = defaultdict(list)
    for default_author in result_2.scalars().all():
        default_authors[default_author.author_id].append(default_author.user_id)

    result_3 = await session.execute(
        select(ArticleModel.author_id, count("*")).group_by(ArticleModel.author_id),
    )
    count_of_articles: dict[AuthorId, int] = defaultdict(lambda: 0)
    for author_id, cnt in result_3.tuples().all():
        count_of_articles[author_id] = cnt

    result_4 = await session.execute(
        select(ArticleDraftModel.author_id, count("*"))
        .where(~ArticleDraftModel.is_published)
        .group_by(ArticleDraftModel.author_id),
    )
    count_of_article_drafts_in_work: dict[AuthorId, int] = defaultdict(lambda: 0)
    for author_id_4, cnt in result_4.tuples().all():
        if author_id_4 is not None:
            count_of_article_drafts_in_work[author_id_4] = cnt

    return AuthorsListSchema(
        authors=[
            AuthorExtendedSchema(
                id=author.id,
                name=author.name,
                is_real_person=author.is_real_person,
                default_for_users=default_authors[author.id],
                count_of_articles=count_of_articles[author.id],
                count_of_article_drafts_in_work=count_of_article_drafts_in_work[
                    author.id
                ],
            )
            for author in authors
        ],
    )


@router.get(path="/{author_id}")
@inject
async def get_author(
    author_id: Annotated[AuthorId, Path(description="ID автора")],
    session: Annotated[AsyncSession, Inject],
    authentication: Authentication,
    edit_authors_permission: Annotated[EditAuthorsPermission, Inject],
) -> AuthorSchema:
    can_edit_authors = await edit_authors_permission.evaluate(
        principal=authentication.principal,
    )
    if not can_edit_authors:
        raise AuthorizationError

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
    authentication: Authentication,
) -> CreateAuthorResponseSchema:
    author = await create_author_command.execute(
        name=name,
        is_real_person=is_real_person,
        principal=authentication.principal,
        agent=authentication.agent,
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
    authentication: Authentication,
) -> UpdateAuthorResponseSchema:
    author = await update_author_command.execute(
        author_id=author_id,
        new_name=name,
        principal=authentication.principal,
        agent=authentication.agent,
    )
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
