from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

ISSUER_LOCAL_AUTHORITY = "LOCAL AUTHORITY"


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
