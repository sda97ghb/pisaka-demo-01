from dataclasses import dataclass

from pisaka.platform.security.claims import (
    AGENT_NAME_LOCAL_CLI,
    AGENT_PLATFORM_NAME_LOCAL_CLI,
    AgentNameClaim,
    AgentPlatformClaim,
    ClaimsIdentity,
)


@dataclass
class AuthenticationResult:
    principal: ClaimsIdentity
    agent: ClaimsIdentity


def authenticate_cli() -> AuthenticationResult:
    return AuthenticationResult(
        principal=ClaimsIdentity(claims=[]),
        agent=ClaimsIdentity(
            claims=[
                AgentNameClaim(agent_name=AGENT_NAME_LOCAL_CLI),
                AgentPlatformClaim(platform_name=AGENT_PLATFORM_NAME_LOCAL_CLI),
            ],
        ),
    )
