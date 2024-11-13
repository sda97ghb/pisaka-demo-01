from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import NewType

import aioinject
from aioinject.ext.fastapi import AioInjectMiddleware
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette import status

from pisaka.platform.security.authorization import AuthorizationError

PublicAPIApp = NewType("PublicAPIApp", FastAPI)


def create_app(container: aioinject.Container) -> PublicAPIApp:
    from pisaka.app import authors

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        async with container:
            yield

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(AioInjectMiddleware, container=container)

    app.include_router(authors.api.router)

    async def handle_authorization_error(_: Request, exception: Exception) -> Response:
        assert isinstance(exception, AuthorizationError)  # noqa: S101
        return JSONResponse(
            content={"reason": "Unauthorized"},
            status_code=status.HTTP_403_FORBIDDEN,
        )

    app.add_exception_handler(AuthorizationError, handle_authorization_error)

    return PublicAPIApp(app)
