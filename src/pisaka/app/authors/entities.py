from pisaka.app.authors.ids import AuthorId
from pisaka.app.authors.models import AuthorModel


class Author:
    def __init__(self, model: AuthorModel) -> None:
        self._model = model

    @classmethod
    def create(
        cls,
        *,
        id_: AuthorId,
        name: str,
        is_real_person: bool,
    ) -> "Author":
        return cls(
            model=AuthorModel(
                id=id_,
                name=name,
                is_real_person=is_real_person,
            ),
        )

    @property
    def id(self) -> AuthorId:
        return self._model.id

    @property
    def name(self) -> str:
        return self._model.name

    @property
    def is_real_person(self) -> bool:
        return self._model.is_real_person

    def set_name(self, name: str) -> None:
        self._model.name = name
