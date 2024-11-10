from typing import Any


class NotFoundError(Exception):
    def __init__(self, entity_type: type | str, key: Any) -> None:  # noqa: ANN401
        if isinstance(entity_type, type):
            entity_type = entity_type.__name__
        super().__init__(f"{entity_type}({key}) is not found")
