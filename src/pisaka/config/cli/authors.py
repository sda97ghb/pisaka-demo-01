# Старайтесь делать здесь как можно меньше импортов, чтобы приложение
# запускалось быстрее. Если каким-то командам не хватает импортов,
# то они должны делать их локально у себя
from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

import aioinject
import anyio
from rich import print
from typer import Argument, Option, Typer

cli = Typer(
    no_args_is_help=True,
    short_help="Авторы",
    help="Команды для работы с модулем авторов",
)


@cli.command()
def create(
    *,
    name: Annotated[str, Argument(help="Имя", show_default=False)],
    is_fake: Annotated[
        bool,
        Option(help="Вымышленный персонаж?", is_flag=True),
    ] = False,
) -> None:
    """Создать автора"""
    from pisaka.app.authors import CreateAuthorCommand
    from pisaka.config.cli.authors_utils import repr_author_as_table
    from pisaka.platform.security.authentication.cli import authenticate_cli

    async def main(ctx: aioinject.InjectionContext) -> None:
        create_author_command = await ctx.resolve(CreateAuthorCommand)
        authentication = authenticate_cli()
        author = await create_author_command.execute(
            name=name,
            is_real_person=not is_fake,
            principal=authentication.principal,
            agent=authentication.agent,
        )
        table = repr_author_as_table(author, "Created author")
        print(table)

    _run(main)


@cli.command()
def update(
    author_id: Annotated[UUID, Argument(help="ID автора", show_default=False)],
    new_name: Annotated[str, Option("--name", help="Новое имя", prompt=True)],
) -> None:
    """Обновить автора"""
    from pisaka.app.authors import AuthorId, UpdateAuthorCommand
    from pisaka.config.cli.authors_utils import repr_author_as_table
    from pisaka.platform.security.authentication.cli import authenticate_cli

    async def main(ctx: aioinject.InjectionContext) -> None:
        update_author_command = await ctx.resolve(UpdateAuthorCommand)
        authentication = authenticate_cli()
        author = await update_author_command.execute(
            author_id=AuthorId(author_id),
            new_name=new_name,
            principal=authentication.principal,
            agent=authentication.agent,
        )
        table = repr_author_as_table(author, "Updated author")
        print(table)

    _run(main)


def _run_in_container(
    container: aioinject.Container,
    fn: Callable[[aioinject.InjectionContext], Awaitable[None]],
) -> None:
    async def main() -> None:
        async with container, container.context() as ctx:
            await fn(ctx)

    anyio.run(main)


def _run(fn: Callable[[aioinject.InjectionContext], Awaitable[None]]) -> None:
    from pisaka.config.config_files import load_config
    from pisaka.config.di import create_base_di_container
    from pisaka.platform.logging import init_logging

    config = load_config()
    init_logging(config.logging)
    container = create_base_di_container(config=config)
    _run_in_container(container, fn)
