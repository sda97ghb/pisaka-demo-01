from typing import Annotated

from typer import Option, Typer

cli = Typer(
    no_args_is_help=True,
    short_help="Разработка и отладка",
    help="Набор вспомогательных команд для разработки и отладки",
)


@cli.command()
def init_db() -> None:
    """Создать пустую БД.

    Создает структуру таблиц, но не заполняет их данными.

    ТОЛЬКО ДЛЯ РАЗРАБОТКИ! Для прода используйте миграции
    """
    from sqlalchemy import Engine

    import pisaka.platform.db
    from pisaka.config.config_files import load_config
    from pisaka.config.di import create_base_di_container
    from pisaka.platform.logging import init_logging

    config = load_config()
    init_logging(config.logging)
    container = create_base_di_container(config=config)
    with container, container.sync_context() as ctx:
        engine: Engine = ctx.resolve(Engine)
        pisaka.platform.db.DBModel.metadata.create_all(bind=engine)


@cli.command()
def jwt() -> None:
    """Создать тестовый JWT."""
    from datetime import datetime, timedelta
    from uuid import uuid4

    import jwt

    from pisaka.config.config_files import load_config

    config = load_config()

    user_id = str(uuid4())
    now = datetime.now()  # noqa: DTZ005

    encoded: str = jwt.encode(
        payload={
            "jti": str(uuid4()),
            "iss": config.internal_api.jwt_authentication.issuer,
            "sub": user_id,
            "iat": now.timestamp(),
            "nbf": now.timestamp(),
            "exp": (now + timedelta(minutes=30)).timestamp(),
            "aud": [config.internal_api.jwt_authentication.audience],
            "azp": "pisaka-frontend",
            "username": "j.doe",
            "email": "j.doe@mail.com",
            "given_name": "John",
            "family_name": "Doe",
        },
        key=config.internal_api.jwt_authentication.private_key,
        algorithm=config.internal_api.jwt_authentication.algorithm,
    )
    print(encoded)  # noqa: T201


@cli.command()
def print_config(
    *,
    is_raw: Annotated[
        bool,
        Option("--raw", is_flag=True, help='Вывести "сырой" конфиг'),
    ] = False,
) -> None:
    """Вывести текущий конфиг.

    Загрузка конфига работает в два этапа:

    1. сначала данные собираются из всех источников и объединяются в одну
    общую структуру (так называемый "сырой" конфиг)

    2. загруженная структура валидируется

    Эта команда по умолчанию выводит итоговый, отвалидированный конфиг.
    Специальным флагом можно запросить вывод "сырого" конфига.
    """
    from pprint import pprint

    from pisaka.config.config_files import load_config, load_raw_config

    if is_raw:
        raw_config = load_raw_config()
        pprint(dict(raw_config))  # noqa: T203
        return

    config = load_config()
    print(config.model_dump_json(indent=2))  # noqa: T201
