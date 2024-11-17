from uuid import uuid4

from pisaka.app.authors import Author, AuthorId


def test_author_create() -> None:
    author_id = AuthorId(uuid4())
    name = "J. Doe"
    is_real_person = True

    author = Author.create(
        id_=author_id,
        name=name,
        is_real_person=is_real_person,
    )

    assert author.id == author_id
    assert author.name == name
    assert author.is_real_person


def test_author_set_name() -> None:
    author = Author.create(
        id_=AuthorId(uuid4()),
        name="J. Doe",
        is_real_person=True,
    )
    new_name = "J. Smith"

    author.set_name(new_name)

    assert author.name == new_name
