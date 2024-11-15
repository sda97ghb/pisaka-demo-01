from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, PrimaryKeyConstraint, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pisaka.app.articles.ids import ArticleDraftId, ArticleId
from pisaka.app.authors import AuthorId
from pisaka.platform.db import DBModel


class ArticleModel(DBModel):
    __tablename__ = "articles"

    id: Mapped[ArticleId] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    author_id: Mapped[AuthorId] = mapped_column(Uuid(as_uuid=True))
    headline: Mapped[str] = mapped_column(String(length=100))
    content: Mapped[str] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(String(length=30))
    disproof: Mapped[str | None] = mapped_column(Text)


class ArticleDraftModel(DBModel):
    __tablename__ = "article_drafts"

    id: Mapped[ArticleDraftId] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    is_published: Mapped[bool] = mapped_column(Boolean)
    author_id: Mapped[AuthorId | None] = mapped_column(Uuid(as_uuid=True))
    headline: Mapped[str] = mapped_column(String(length=100))
    content: Mapped[str] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(String(length=30))
    auto_slug: Mapped[bool] = mapped_column(Boolean)
    editors: Mapped[list["ArticleDraftEditorModel"]] = relationship(
        "ArticleDraftEditorModel",
    )


class ArticleDraftEditorModel(DBModel):
    __tablename__ = "article_draft_editors"
    __table_args__ = (
        PrimaryKeyConstraint(
            "article_draft_id",
            "user_id",
            name="article_draft_editors_pk",
        ),
    )

    article_draft_id: Mapped[ArticleDraftId] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            column="article_drafts.id",
            name="article_draft_editors_draft_id_fk",
        ),
    )
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True))
