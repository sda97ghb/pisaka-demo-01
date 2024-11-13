from pisaka.platform.security.claims import (
    AGENT_NAME_LOCAL_CLI,
    AGENT_NAME_TESTS,
    AgentNameClaim,
    ClaimsIdentity,
    PisakaRoleClaim,
)
from pisaka.platform.security.roles import PisakaRole


class EditAuthorsPermission:
    async def evaluate(self, principal: ClaimsIdentity) -> bool:
        for role_claim in principal.find_all(PisakaRoleClaim):
            if role_claim.role == PisakaRole.CHIEF:
                return True
        return False


class AlmightyLocalCliPermission:
    async def evaluate(self, agent: ClaimsIdentity) -> bool:
        agent_name_claim = agent.find_first(AgentNameClaim)
        return (
            agent_name_claim is not None
            and agent_name_claim.agent_name == AGENT_NAME_LOCAL_CLI
        )


class AlmightyTestsPermission:
    async def evaluate(self, agent: ClaimsIdentity) -> bool:
        agent_name_claim = agent.find_first(AgentNameClaim)
        return (
            agent_name_claim is not None
            and agent_name_claim.agent_name == AGENT_NAME_TESTS
        )
