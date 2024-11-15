from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from pisaka.app.articles.db import ArticleDraftModel, ArticleModel
from pisaka.app.articles.entities import Article, ArticleDraft
from pisaka.app.articles.ids import ArticleDraftId, ArticleId
from pisaka.platform.errors import NotFoundError


class ArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, article_id: ArticleId) -> Article:
        result = await self._session.execute(
            select(ArticleModel).where(ArticleModel.id == article_id).with_for_update(),
        )
        model: ArticleModel | None = result.scalar_one_or_none()
        if model is None:
            raise NotFoundError(entity_type=Article, key=article_id)
        return Article(model=model)

    async def save(self, article: Article) -> None:
        model = article._model  # noqa: SLF001
        self._session.add(model)
        await self._session.flush([model])

    async def delete(self, article_id: ArticleId) -> None:
        await self._session.execute(
            delete(ArticleModel).where(ArticleModel.id == article_id),
        )


class ArticleDraftRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, article_draft_id: ArticleDraftId) -> ArticleDraft:
        result = await self._session.execute(
            select(ArticleDraftModel)
            .where(ArticleDraftModel.id == article_draft_id)
            .with_for_update(),
        )
        model: ArticleDraftModel | None = result.scalar_one_or_none()
        if model is None:
            raise NotFoundError(entity_type=ArticleDraft, key=article_draft_id)
        return ArticleDraft(model=model)

    async def save(self, article_draft: ArticleDraft) -> None:
        model = article_draft._model  # noqa: SLF001
        self._session.add(model)
        await self._session.flush([model])

    async def delete(self, article_draft_id: ArticleDraftId) -> None:
        await self._session.execute(
            delete(ArticleDraftModel).where(ArticleDraftModel.id == article_draft_id),
        )
