from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated

import jwt
from aioinject import Inject
from aioinject.ext.fastapi import inject
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from pydantic import BaseModel, ValidationError
from starlette import status

from security.claims import (
    Claim,
    ClaimsIdentity,
    EmailClaim,
    FirstNameClaim,
    LastNameClaim,
    UserIdClaim,
    UsernameClaim,
)


class AuthenticationError(HTTPException):
    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=reason,
        )


@dataclass(kw_only=True)
class JWTAuthenticationOptions:
    public_key: str
    audience: str
    issuer: str
    algorithm: str = "RS256"
    leeway_sec: int = 60


class _JWTClaimsSchema(BaseModel):
    sub: str
    username: str | None
    email: str | None
    given_name: str | None
    family_name: str | None


async def _validate_jwt_or_raise_authentication_error(
    token: str,
    options: JWTAuthenticationOptions,
) -> _JWTClaimsSchema:
    try:
        return _JWTClaimsSchema.model_validate(
            jwt.decode(
                jwt=token,
                key=options.public_key,
                algorithms=[options.algorithm],
                options={
                    "verify_signature": True,
                    "require": ["aud", "exp", "iss", "sub"],
                    "verify_aud": True,
                    "verify_exp": True,
                    "verify_iss": True,
                },
                verify=True,
                audience=options.audience,
                issuer=options.issuer,
                leeway=timedelta(seconds=options.leeway_sec),
            ),
        )
    except PyJWTError as err:
        raise AuthenticationError("Invalid JWT") from err
    except ValidationError as err:
        raise AuthenticationError("Invalid JWT") from err


def _build_identity(issuer: str, jwt_claims: _JWTClaimsSchema) -> ClaimsIdentity:
    identity_claims: list[Claim] = [
        UserIdClaim(issuer=issuer, user_id=jwt_claims.sub),
    ]
    if username := jwt_claims.username:
        identity_claims.append(UsernameClaim(issuer=issuer, username=username))
    if email := jwt_claims.email:
        identity_claims.append(EmailClaim(issuer=issuer, email=email))
    if first_name := jwt_claims.given_name:
        identity_claims.append(FirstNameClaim(issuer=issuer, first_name=first_name))
    if last_name := jwt_claims.family_name:
        identity_claims.append(LastNameClaim(issuer=issuer, last_name=last_name))
    return ClaimsIdentity(claims=identity_claims)


@dataclass
class AuthenticationResult:
    principal: ClaimsIdentity


@inject
async def _authenticate(
    http_cred: Annotated[
        HTTPAuthorizationCredentials,
        Depends(
            HTTPBearer(
                bearerFormat="JWT",
                scheme_name="HTTPBearerJWT",
                description="JWT in HTTP header Authorization with Bearer scheme",
            ),
        ),
    ],
    jwt_auth_opt: Annotated[JWTAuthenticationOptions, Inject],
) -> AuthenticationResult:
    jwt_claims = await _validate_jwt_or_raise_authentication_error(
        token=http_cred.credentials,
        options=jwt_auth_opt,
    )
    principal = _build_identity(issuer=jwt_auth_opt.issuer, jwt_claims=jwt_claims)
    return AuthenticationResult(principal=principal)


Authentication = Annotated[AuthenticationResult, Depends(_authenticate)]
