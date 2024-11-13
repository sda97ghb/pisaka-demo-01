from dataclasses import dataclass

from pisaka.platform.security.claims import (
    AGENT_NAME_TESTS,
    AGENT_PLATFORM_NAME_PYTEST,
    AgentNameClaim,
    AgentPlatformClaim,
    ClaimsIdentity,
)


@dataclass
class AuthenticationResult:
    principal: ClaimsIdentity
    agent: ClaimsIdentity


def authenticate_almighty() -> AuthenticationResult:
    return AuthenticationResult(
        principal=ClaimsIdentity(claims=[]),
        agent=ClaimsIdentity(
            claims=[
                AgentNameClaim(agent_name=AGENT_NAME_TESTS),
                AgentPlatformClaim(platform_name=AGENT_PLATFORM_NAME_PYTEST),
            ],
        ),
    )
