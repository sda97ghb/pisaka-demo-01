from collections.abc import Iterable
from typing import Final
from uuid import UUID

from pisaka.platform.security.claims import (
    AGENT_NAME_TESTS,
    AGENT_PLATFORM_NAME_PYTEST,
    AgentNameClaim,
    AgentPlatformClaim,
    ClaimsIdentity,
    PisakaRoleClaim,
    UserIdClaim,
)


def has_any_role(principal: ClaimsIdentity, roles: Iterable[str]) -> bool:
    for role_claim in principal.find_all(PisakaRoleClaim):
        if role_claim.role in roles:
            return True
    return False


def has_role(principal: ClaimsIdentity, role: str) -> bool:
    return has_any_role(principal=principal, roles=[role])


def has_all_roles(principal: ClaimsIdentity, roles: Iterable[str]) -> bool:
    has_roles = [role_claim.role for role_claim in principal.find_all(PisakaRoleClaim)]
    missing_roles = set(roles) - set(has_roles)
    return not missing_roles


class NoUserIdClaimError(Exception):
    def __init__(self) -> None:
        super().__init__("no user id claim")


def get_user_id(principal: ClaimsIdentity) -> UUID:
    user_id_claim = principal.find_first(UserIdClaim)
    if user_id_claim is None:
        raise NoUserIdClaimError
    return user_id_claim.user_id


PRINCIPAL_DOES_NOT_MATTER: Final[ClaimsIdentity] = ClaimsIdentity(claims=[])
AGENT_FOR_TESTS: Final[ClaimsIdentity] = ClaimsIdentity(
    claims=[
        AgentNameClaim(agent_name=AGENT_NAME_TESTS),
        AgentPlatformClaim(platform_name=AGENT_PLATFORM_NAME_PYTEST),
    ],
)
