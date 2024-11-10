from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Annotated, Any
from uuid import uuid4

import jwt
from aioinject import Inject
from aioinject.ext.fastapi import inject
from fastapi import Depends, Request, HTTPException
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.base import SecurityBase
from jwt import InvalidIssuerError, PyJWTError
from pydantic import BaseModel, ValidationError
from starlette import status

from security.claims import ClaimsIdentity, UserIdClaim, UsernameClaim, EmailClaim, \
    FirstNameClaim, LastNameClaim


"""
# try:
#     decoded = jwt.decode(
#         jwt=encoded,
#         key=public_key,
#         algorithms=["RS256"],
#         options={
#             "verify_signature": True,
#             "require": ["aud", "exp", "iss", "sub"],
#             "verify_aud": True,
#             "verify_exp": True,
#             "verify_iss": True,
#         },
#         verify=True,
#         audience=audience,
#         issuer=issuer,
#         leeway=timedelta(seconds=60),
#     )
# except PyJWTError as err:
#     print(f"invalid token, not authenticated: {err}")
"""


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


class JWTClaimsSchema(BaseModel):
    sub: str
    username: str | None
    email: str | None
    given_name: str | None
    family_name: str | None


class JWTAuthentication:
    def __init__(self, options: JWTAuthenticationOptions) -> None:
        self._options = options

    async def authenticate(self, token: str) -> ClaimsIdentity:
        try:
            jwt_claims = JWTClaimsSchema.model_validate(
                jwt.decode(
                    jwt=token,
                    key=self._options.public_key,
                    algorithms=[self._options.algorithm],
                    options={
                        "verify_signature": True,
                        "require": ["aud", "exp", "iss", "sub"],
                        "verify_aud": True,
                        "verify_exp": True,
                        "verify_iss": True,
                    },
                    verify=True,
                    audience=self._options.audience,
                    issuer=self._options.issuer,
                    leeway=timedelta(seconds=self._options.leeway_sec),
                )
            )
        except (PyJWTError | ValidationError) as err:
            raise AuthenticationError("Invalid JWT") from err
        return self._build_identity(jwt_claims)

    def _build_identity(self, jwt_claims: JWTClaimsSchema) -> ClaimsIdentity:
        issuer = self._options.issuer
        identity_claims = [
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


@inject
async def authenticate_principal(
    auth: Annotated[JWTAuthentication, Inject],
    http_cred: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(
            bearerFormat="JWT",
            scheme_name="HTTPBearerJWT",
            description="JWT in HTTP header Authorization with Bearer scheme",
        )
    ),
) -> ClaimsIdentity:
    print("APIKEY:", http_cred)
    principal = await auth.authenticate(http_cred.credentials)
    print("Principal:", principal)
    return principal


@dataclass
class AuthenticationResult:
    principal: ClaimsIdentity


@inject
async def _authenticate(
    auth: Annotated[JWTAuthentication, Inject],
    http_cred: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(
            bearerFormat="JWT",
            scheme_name="HTTPBearerJWT",
            description="JWT in HTTP header Authorization with Bearer scheme",
        )
    ),
) -> AuthenticationResult:
    print("APIKEY:", http_cred)
    principal = await auth.authenticate(http_cred.credentials)
    print("Principal:", principal)
    return AuthenticationResult(principal=principal)


Authentication = Annotated[AuthenticationResult, Depends(_authenticate)]

# principal: Annotated[ClaimsIdentity, Depends(authenticate)]
