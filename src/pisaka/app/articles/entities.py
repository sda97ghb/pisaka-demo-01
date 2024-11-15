from dataclasses import dataclass
from uuid import UUID

from pisaka.app.articles.db import (
    ArticleDraftEditorModel,
    ArticleDraftModel,
    ArticleModel,
)
from pisaka.app.articles.ids import ArticleDraftId, ArticleId
from pisaka.app.articles.slug import is_valid_slug, slugify
from pisaka.app.authors import AuthorId


class Article:
    def __init__(self, model: ArticleModel) -> None:
        self._model = model

    @classmethod
    def create(
        cls,
        id_: ArticleId,
        author_id: AuthorId,
        headline: str,
        content: str,
        slug: str,
    ) -> "Article":
        return cls(
            model=ArticleModel(
                id=id_,
                author_id=author_id,
                headline=headline,
                content=content,
                slug=slug,
                disproof=None,
            ),
        )

    @property
    def id(self) -> ArticleId:
        return self._model.id

    @property
    def author_id(self) -> AuthorId:
        return self._model.author_id

    @property
    def headline(self) -> str:
        return self._model.headline

    @property
    def content(self) -> str:
        return self._model.content

    @property
    def slug(self) -> str:
        return self._model.slug

    @property
    def disproof(self) -> str | None:
        return self._model.disproof

    def disprove(self, disproof: str) -> None:
        self._model.disproof = disproof


class ArticleDraft:
    def __init__(self, model: ArticleDraftModel) -> None:
        self._model = model

    @classmethod
    def create_from_scratch(
        cls,
        *,
        id_: ArticleDraftId,
        author_id: AuthorId | None = None,
        created_by_user_id: UUID,
    ) -> "ArticleDraft":
        return cls(
            model=ArticleDraftModel(
                id=id_,
                is_published=False,
                author_id=author_id,
                headline="",
                content="",
                slug="",
                auto_slug=True,
                editors=[
                    ArticleDraftEditorModel(
                        article_draft_id=id_,
                        user_id=created_by_user_id,
                    ),
                ],
            ),
        )

    @property
    def id(self) -> ArticleDraftId:
        return self._model.id

    @property
    def is_published(self) -> bool:
        return self._model.is_published

    @property
    def author_id(self) -> AuthorId | None:
        return self._model.author_id

    @author_id.setter
    def author_id(self, new_author_id: AuthorId) -> None:
        self._model.author_id = new_author_id

    @property
    def headline(self) -> str:
        return self._model.headline

    @headline.setter
    def headline(self, new_headline: str) -> None:
        self._model.headline = new_headline
        if self._model.auto_slug:
            self._model.slug = slugify(self._model.headline)

    @property
    def content(self) -> str:
        return self._model.content

    @property
    def slug(self) -> str:
        return self._model.slug

    @slug.setter
    def slug(self, new_slug: str) -> None:
        if self._model.auto_slug:
            raise Exception(  # noqa: TRY002
                "can not update slug when auto_slug is enabled",
            )
        self._model.slug = new_slug

    @property
    def auto_slug(self) -> bool:
        return self._model.auto_slug

    def enable_auto_slug(self) -> None:
        self._model.auto_slug = True
        self._model.slug = slugify(self._model.headline)

    def disable_auto_slug(self) -> None:
        self._model.auto_slug = False

    def is_editor(self, user_id: UUID) -> bool:
        return any(editor.user_id == user_id for editor in self._model.editors)

    @dataclass
    class ValidDraft:
        author_id: AuthorId
        headline: str
        content: str
        slug: str

    @dataclass
    class DraftIsInvalid:
        problems: list[str]

    def validate(self) -> ValidDraft | DraftIsInvalid:
        problems = []

        author_id = self._model.author_id
        if author_id is None:
            problems.append("no author is set")

        headline = self._model.headline.strip()
        if not headline:
            problems.append("no headline")

        content = self._model.content.strip()
        if not content:
            problems.append("no content")

        slug = self._model.slug.strip()
        if not is_valid_slug(slug):
            problems.append("invalid slug")

        if problems:
            return self.DraftIsInvalid(problems=problems)

        assert author_id is not None  # noqa: S101

        return self.ValidDraft(
            author_id=author_id,
            headline=headline,
            content=content,
            slug=slug,
        )

    def mark_published(self) -> None:
        self._model.is_published = True
