from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import NewType

import aioinject
from aioinject.ext.fastapi import AioInjectMiddleware
from fastapi import FastAPI

PublicAPIApp = NewType("PublicAPIApp", FastAPI)


def create_app(container: aioinject.Container) -> PublicAPIApp:
    from pisaka import authors

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        async with container:
            yield

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(AioInjectMiddleware, container=container)

    app.include_router(authors.api.router)

    return PublicAPIApp(app)
