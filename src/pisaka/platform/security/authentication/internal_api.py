from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated
from uuid import UUID

import jwt
from aioinject import Inject
from aioinject.ext.fastapi import inject
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from pydantic import BaseModel, ValidationError
from starlette import status

from pisaka.platform.security.authentication.common import JWTAuthenticationOptions
from pisaka.platform.security.claims import (
    ISSUER_LOCAL_AUTHORITY,
    AgentNameClaim,
    AgentPlatformClaim,
    Claim,
    ClaimsIdentity,
    EmailClaim,
    FirstNameClaim,
    LastNameClaim,
    PisakaRoleClaim,
    UserIdClaim,
    UsernameClaim,
)


class _JWTClaimsSchema(BaseModel):
    iss: str
    sub: str
    username: str | None
    email: str | None
    given_name: str | None
    family_name: str | None
    azp: str | None
    client_roles: dict[str, list[str]] | None


@dataclass
class AuthenticationResult:
    principal: ClaimsIdentity
    agent: ClaimsIdentity


@inject
async def _authenticate(
    request: Request,
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
    try:
        jwt_claims = _JWTClaimsSchema.model_validate(
            jwt.decode(
                jwt=http_cred.credentials,
                key=jwt_auth_opt.public_key,
                algorithms=[jwt_auth_opt.algorithm],
                options={
                    "verify_signature": True,
                    "require": ["aud", "exp", "iss", "sub"],
                    "verify_aud": True,
                    "verify_exp": True,
                    "verify_iss": True,
                },
                verify=True,
                audience=jwt_auth_opt.audience,
                issuer=jwt_auth_opt.issuer,
                leeway=timedelta(seconds=jwt_auth_opt.leeway_sec),
            ),
        )
    except (PyJWTError, ValidationError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT",
        ) from err

    jwt_issuer = jwt_claims.iss

    principal_claims: list[Claim] = [
        UserIdClaim(issuer=jwt_issuer, user_id=UUID(jwt_claims.sub)),
    ]
    if username := jwt_claims.username:
        principal_claims.append(UsernameClaim(issuer=jwt_issuer, username=username))
    if email := jwt_claims.email:
        principal_claims.append(EmailClaim(issuer=jwt_issuer, email=email))
    if first_name := jwt_claims.given_name:
        principal_claims.append(
            FirstNameClaim(issuer=jwt_issuer, first_name=first_name),
        )
    if last_name := jwt_claims.family_name:
        principal_claims.append(LastNameClaim(issuer=jwt_issuer, last_name=last_name))
    if (client_roles := jwt_claims.client_roles) and (
        pisaka_roles := client_roles.get("pisaka-backend")
    ):
        for role in pisaka_roles:
            principal_claims.append(PisakaRoleClaim(issuer=jwt_issuer, role=role))
    principal = ClaimsIdentity(claims=principal_claims)

    agent_claims: list[Claim] = []
    if user_agent := request.headers.get("User-Agent"):
        agent_claims.append(
            AgentPlatformClaim(issuer=ISSUER_LOCAL_AUTHORITY, platform_name=user_agent),
        )
    if authorized_party := jwt_claims.azp:
        agent_claims.append(
            AgentNameClaim(issuer=jwt_issuer, agent_name=authorized_party),
        )
    agent = ClaimsIdentity(claims=agent_claims)

    return AuthenticationResult(principal=principal, agent=agent)


Authentication = Annotated[AuthenticationResult, Depends(_authenticate)]
