import aioinject
from starlette.types import ASGIApp

from pisaka.config.config_files import Config, load_config
from pisaka.config.di import create_base_di_container
from pisaka.platform.logging import init_logging
from pisaka.platform.security.authentication.common import JWTAuthenticationOptions


def public_api_app() -> ASGIApp:
    from pisaka.app.api import create_app

    config = load_config()

    init_logging(config.logging)

    def _create_jwt_authentication_options(config: Config) -> JWTAuthenticationOptions:
        return JWTAuthenticationOptions(
            public_key=config.api.jwt_authentication.public_key,
            audience=config.api.jwt_authentication.audience,
            issuer=config.api.jwt_authentication.issuer,
            algorithm=config.api.jwt_authentication.algorithm,
            leeway_sec=config.api.jwt_authentication.leeway_sec,
        )

    container = create_base_di_container(config=config)
    container.register(aioinject.Singleton(_create_jwt_authentication_options))
    return create_app(container=container)
