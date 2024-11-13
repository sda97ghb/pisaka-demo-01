from dataclasses import dataclass
from typing import Final, TypeVar
from uuid import UUID

ISSUER_LOCAL_AUTHORITY: Final[str] = "LOCAL AUTHORITY"


@dataclass(frozen=True, kw_only=True)
class Claim:
    issuer: str = ISSUER_LOCAL_AUTHORITY


@dataclass(frozen=True, kw_only=True)
class UserIdClaim(Claim):
    user_id: UUID


@dataclass(frozen=True, kw_only=True)
class UsernameClaim(Claim):
    username: str


@dataclass(frozen=True, kw_only=True)
class EmailClaim(Claim):
    email: str


@dataclass(frozen=True, kw_only=True)
class FirstNameClaim(Claim):
    first_name: str


@dataclass(frozen=True, kw_only=True)
class LastNameClaim(Claim):
    last_name: str


@dataclass(frozen=True, kw_only=True)
class PisakaRoleClaim(Claim):
    role: str


AGENT_NAME_LOCAL_CLI: Final[str] = "LOCAL CLI"
AGENT_NAME_TESTS: Final[str] = "TESTS"


@dataclass(frozen=True, kw_only=True)
class AgentNameClaim(Claim):
    agent_name: str


AGENT_PLATFORM_NAME_LOCAL_CLI: Final[str] = "LOCAL CLI"
AGENT_PLATFORM_NAME_PYTEST: Final[str] = "PYTEST"


@dataclass(frozen=True, kw_only=True)
class AgentPlatformClaim(Claim):
    platform_name: str


ClaimT = TypeVar("ClaimT", bound=Claim)


@dataclass(frozen=True)
class ClaimsIdentity:
    claims: list[Claim]

    def find_first(self, claim_type: type[ClaimT]) -> ClaimT | None:
        for claim in self.claims:
            if isinstance(claim, claim_type):
                return claim
        return None

    def find_all(self, claim_type: type[ClaimT]) -> list[ClaimT]:
        return [claim for claim in self.claims if isinstance(claim, claim_type)]
