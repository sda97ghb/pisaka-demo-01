from pisaka.platform.security.claims import (
    AgentNameClaim,
    ClaimsIdentity,
    PisakaRoleClaim,
)
from pisaka.platform.security.roles import PisakaRole
from pisaka.platform.security.utils import has_any_role


class ListAuthorsPermission:
    def __init__(self, agent_name_admin_panel: str) -> None:
        self._agent_name_admin_panel = agent_name_admin_panel

    async def evaluate(self, principal: ClaimsIdentity, agent: ClaimsIdentity) -> bool:
        agent_name_claim = agent.find_first(AgentNameClaim)
        agent_name = agent_name_claim.agent_name if agent_name_claim else None
        if agent_name == self._agent_name_admin_panel:
            return has_any_role(
                principal=principal,
                roles=[PisakaRole.JOURNALIST, PisakaRole.EDITOR, PisakaRole.CHIEF],
            )
        return False


class EditAuthorsPermission:
    async def evaluate(self, principal: ClaimsIdentity) -> bool:
        for role_claim in principal.find_all(PisakaRoleClaim):
            if role_claim.role == PisakaRole.CHIEF:
                return True
        return False
