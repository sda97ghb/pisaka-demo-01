from uuid import UUID

from sqlalchemy import Boolean, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from pisaka.authors.ids import AuthorId
from pisaka.db import DBModel


class AuthorModel(DBModel):
    __tablename__ = "authors"

    id: Mapped[AuthorId] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(length=30))
    is_real_person: Mapped[bool] = mapped_column(Boolean)


class DefaultAuthorModel(DBModel):
    __tablename__ = "default_author"

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    author_id: Mapped[AuthorId] = mapped_column(Uuid(as_uuid=True))
