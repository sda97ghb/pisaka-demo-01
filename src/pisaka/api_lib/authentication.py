from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated
from uuid import UUID

import jwt
from aioinject import Inject
from aioinject.ext.fastapi import inject
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from pydantic import BaseModel, ValidationError
from starlette import status

from security.authentication import JWTAuthenticationOptions
from security.claims import Claim, ClaimsIdentity, EmailClaim, UserIdClaim


class _JWTClaimsSchema(BaseModel):
    sub: str
    email: str | None


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

    issuer = jwt_auth_opt.issuer
    identity_claims: list[Claim] = [
        UserIdClaim(issuer=issuer, user_id=UUID(jwt_claims.sub)),
    ]
    if email := jwt_claims.email:
        identity_claims.append(EmailClaim(issuer=issuer, email=email))
    principal = ClaimsIdentity(claims=identity_claims)

    return AuthenticationResult(principal=principal)


Authentication = Annotated[AuthenticationResult, Depends(_authenticate)]
