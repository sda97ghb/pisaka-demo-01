from collections.abc import AsyncGenerator

import aioinject
import pytest

from pisaka.app.authors import CreateAuthorCommand
from pisaka.config.config_files import load_config
from pisaka.config.di import create_base_di_container
from pisaka.platform.logging import init_logging
from pisaka.platform.security.utils import AGENT_FOR_TESTS, PRINCIPAL_DOES_NOT_MATTER

pytestmark = [pytest.mark.anyio]


@pytest.fixture
async def di_container() -> AsyncGenerator[aioinject.Container, None]:
    config = load_config()
    init_logging(config.logging)
    container = create_base_di_container(config)
    async with container:
        yield container


@pytest.fixture
async def ctx(
    di_container: aioinject.Container,
) -> AsyncGenerator[aioinject.InjectionContext, None]:
    async with di_container.context() as ctx:
        yield ctx


async def test_execute(ctx: aioinject.InjectionContext) -> None:
    command = await ctx.resolve(CreateAuthorCommand)
    author = await command.execute(
        name="J. Doe",
        is_real_person=True,
        principal=PRINCIPAL_DOES_NOT_MATTER,
        agent=AGENT_FOR_TESTS,
    )

    assert author.name == "J. Doe"
    assert author.is_real_person
