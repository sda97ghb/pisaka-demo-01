from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from pisaka.app.articles.entities import Article, ArticleDraft
from pisaka.app.articles.ids import ArticleDraftId, ArticleId
from pisaka.app.articles.repositories import ArticleDraftRepository, ArticleRepository
from pisaka.app.articles.security import (
    ROLES_ALLOWED_TO_EDIT_ARTICLE_DRAFTS,
    PublishArticlePermission,
)
from pisaka.app.authors import DefaultAuthorService
from pisaka.platform.security.authorization import AuthorizationError
from pisaka.platform.security.claims import ClaimsIdentity
from pisaka.platform.security.permissions import (
    AlmightyLocalCliPermission,
    AlmightyTestsPermission,
)
from pisaka.platform.security.roles import PisakaRole
from pisaka.platform.security.utils import get_user_id, has_any_role, has_role


class CreateArticleDraftCommand:
    def __init__(
        self,
        article_draft_repository: ArticleDraftRepository,
        session: AsyncSession,
        default_author_service: DefaultAuthorService,
    ) -> None:
        self._repo = article_draft_repository
        self._session = session
        self._default_author_service = default_author_service

    async def execute(self, principal: ClaimsIdentity) -> ArticleDraft:
        await self._authorize(principal=principal)
        user_id = get_user_id(principal)
        author_id = await self._default_author_service.get(user_id=user_id)
        async with self._session.begin():
            draft = ArticleDraft.create_from_scratch(
                id_=ArticleDraftId(uuid4()),
                author_id=author_id,
                created_by_user_id=user_id,
            )
            await self._repo.save(draft)
            return draft

    async def _authorize(self, principal: ClaimsIdentity) -> None:
        if has_any_role(principal, ROLES_ALLOWED_TO_EDIT_ARTICLE_DRAFTS):
            return
        raise AuthorizationError


class UpdateArticleDraftHeadlineCommand:
    def __init__(
        self,
        article_draft_repository: ArticleDraftRepository,
        session: AsyncSession,
        almighty_local_cli_permission: AlmightyLocalCliPermission,
        almighty_tests_permission: AlmightyTestsPermission,
    ) -> None:
        self._repo = article_draft_repository
        self._session = session
        self._almighty_local_cli_permission = almighty_local_cli_permission
        self._almighty_tests_permission = almighty_tests_permission

    async def execute(
        self,
        article_draft_id: ArticleDraftId,
        new_headline: str,
        principal: ClaimsIdentity,
        agent: ClaimsIdentity,
    ) -> ArticleDraft:
        async with self._session.begin():
            draft = await self._repo.get(article_draft_id=article_draft_id)
            await self._authorize(principal=principal, agent=agent, draft=draft)
            draft.headline = new_headline
            await self._repo.save(draft)
            return draft

    async def _authorize(
        self,
        principal: ClaimsIdentity,
        agent: ClaimsIdentity,
        draft: ArticleDraft,
    ) -> None:
        if await self._almighty_local_cli_permission.evaluate(
            agent=agent,
        ) or await self._almighty_tests_permission.evaluate(agent=agent):
            return
        if has_role(principal=principal, role=PisakaRole.CHIEF):
            return
        if not has_any_role(principal, ROLES_ALLOWED_TO_EDIT_ARTICLE_DRAFTS):
            raise AuthorizationError
        user_id = get_user_id(principal=principal)
        if draft.is_editor(user_id):
            return
        raise AuthorizationError


class PublishArticleCommand:
    def __init__(
        self,
        article_draft_repository: ArticleDraftRepository,
        article_repository: ArticleRepository,
        session: AsyncSession,
        almighty_local_cli_permission: AlmightyLocalCliPermission,
        almighty_tests_permission: AlmightyTestsPermission,
        publish_article_permission: PublishArticlePermission,
    ) -> None:
        self._draft_repo = article_draft_repository
        self._article_repo = article_repository
        self._session = session
        self._almighty_local_cli_permission = almighty_local_cli_permission
        self._almighty_tests_permission = almighty_tests_permission
        self._publish_article_permission = publish_article_permission

    async def execute(
        self,
        article_draft_id: ArticleDraftId,
        principal: ClaimsIdentity,
        agent: ClaimsIdentity,
    ) -> Article:
        async with self._session.begin():
            draft = await self._draft_repo.get(article_draft_id=article_draft_id)

            await self._authorize(principal=principal, agent=agent, draft=draft)

            valid_draft_or_problems = draft.validate()
            if isinstance(valid_draft_or_problems, ArticleDraft.DraftIsInvalid):
                raise Exception(  # noqa: TRY002, TRY004
                    f"Invalid draft: {valid_draft_or_problems.problems}",
                )
            valid_draft = valid_draft_or_problems

            article = Article.create(
                id_=ArticleId(uuid4()),
                author_id=valid_draft.author_id,
                headline=valid_draft.headline,
                content=valid_draft.content,
                slug=valid_draft.slug,
            )
            await self._article_repo.save(article)

            draft.mark_published()
            await self._draft_repo.save(draft)

            return article

    async def _authorize(
        self,
        principal: ClaimsIdentity,
        agent: ClaimsIdentity,
        draft: ArticleDraft,
    ) -> None:
        if await self._almighty_local_cli_permission.evaluate(
            agent=agent,
        ) or await self._almighty_tests_permission.evaluate(agent=agent):
            return
        if self._publish_article_permission.evaluate(
            principal=principal,
            article_draft=draft,
        ):
            return
        raise AuthorizationError
