class AuthorizationError(Exception):
    def __init__(self) -> None:
        super().__init__("Доступ запрещен для текущего пользователя")
