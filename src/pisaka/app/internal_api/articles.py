from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from aioinject import Inject
from aioinject.ext.fastapi import inject
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from pisaka.app.articles.commands import CreateArticleDraftCommand
from pisaka.app.articles.db import ArticleDraftModel
from pisaka.app.articles.ids import ArticleDraftId
from pisaka.app.articles.security import ListArticleDraftsPermission
from pisaka.app.authors import AuthorId, AuthorModel
from pisaka.platform.api import BaseSchema
from pisaka.platform.security.authentication.internal_api import Authentication
from pisaka.platform.security.authorization import AuthorizationError

router = APIRouter(
    tags=["Статьи"],
)


class ArtileDraftsListSchema(BaseSchema):
    class Item(BaseSchema):
        class Author(BaseSchema):
            id: AuthorId
            name: str

        id: ArticleDraftId
        is_published: bool
        author: Author | None
        headline: str
        editors: list[UUID]

    drafts: list[Item]


@router.get(path="/article-drafts")
@inject
async def get_article_drafts_list(
    session: Annotated[AsyncSession, Inject],
    authentication: Authentication,
    list_article_drafts_permission: Annotated[ListArticleDraftsPermission, Inject],
) -> ArtileDraftsListSchema:
    can_list_drafts = await list_article_drafts_permission.evaluate(
        principal=authentication.principal,
    )
    if not can_list_drafts:
        raise AuthorizationError

    result = await session.execute(
        select(ArticleDraftModel, AuthorModel)
        .join(AuthorModel, AuthorModel.id == ArticleDraftModel.author_id, isouter=True)
        .options(selectinload(ArticleDraftModel.editors)),
    )
    drafts: Sequence[tuple[ArticleDraftModel, AuthorModel]] = result.tuples().all()

    return ArtileDraftsListSchema(
        drafts=[
            ArtileDraftsListSchema.Item(
                id=draft.id,
                is_published=draft.is_published,
                author=(
                    ArtileDraftsListSchema.Item.Author(
                        id=author.id,
                        name=author.name,
                    )
                    if author
                    else None
                ),
                headline=draft.headline,
                editors=[editor.user_id for editor in draft.editors],
            )
            for draft, author in drafts
        ],
    )


class DraftSchema(BaseSchema):
    id: ArticleDraftId
    author_id: AuthorId | None
    headline: str
    content: str
    slug: str
    auto_slug: bool


class CreateArticleDraftResponseSchema(BaseSchema):
    draft: DraftSchema


@router.post(path="/article-drafts")
@inject
async def create_article_draft(
    create_article_draft_command: Annotated[CreateArticleDraftCommand, Inject],
    authentication: Authentication,
) -> CreateArticleDraftResponseSchema:
    draft = await create_article_draft_command.execute(
        principal=authentication.principal,
    )
    return CreateArticleDraftResponseSchema(draft=DraftSchema.model_validate(draft))
