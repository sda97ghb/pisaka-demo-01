from pisaka.platform.security.claims import (
    AGENT_NAME_LOCAL_CLI,
    AGENT_NAME_TESTS,
    ISSUER_LOCAL_AUTHORITY,
    AgentNameClaim,
    ClaimsIdentity,
)


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
            and agent_name_claim.issuer == ISSUER_LOCAL_AUTHORITY
            and agent_name_claim.agent_name == AGENT_NAME_TESTS
        )
