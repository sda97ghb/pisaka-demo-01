from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from pisaka.app.authors.entities import Author
from pisaka.app.authors.ids import AuthorId
from pisaka.app.authors.permissions import (
    AlmightyLocalCliPermission,
    AlmightyTestsPermission,
    EditAuthorsPermission,
)
from pisaka.app.authors.repositories import AuthorRepository
from pisaka.app.authors.services import DefaultAuthorService
from pisaka.platform.security.authorization import AuthorizationError
from pisaka.platform.security.claims import (
    AGENT_NAME_LOCAL_CLI,
    AGENT_NAME_TESTS,
    AgentNameClaim,
    ClaimsIdentity,
    PisakaRoleClaim,
)
from pisaka.platform.security.roles import PisakaRole


class CreateAuthorCommand:
    def __init__(
        self,
        author_repository: AuthorRepository,
        session: AsyncSession,
        edit_authors_permission: EditAuthorsPermission,
        almighty_local_cli_permission: AlmightyLocalCliPermission,
        almighty_tests_permission: AlmightyTestsPermission,
    ) -> None:
        self._author_repository = author_repository
        self._session = session
        self._edit_authors_permission = edit_authors_permission
        self._almighty_local_cli_permission = almighty_local_cli_permission
        self._almighty_tests_permission = almighty_tests_permission

    async def execute(
        self,
        *,
        name: str,
        is_real_person: bool,
        principal: ClaimsIdentity,
        agent: ClaimsIdentity,
    ) -> Author:
        await self._authorize(principal=principal, agent=agent)
        async with self._session.begin():
            author = Author.create(
                id_=AuthorId(uuid4()),
                name=name,
                is_real_person=is_real_person,
            )
            await self._author_repository.save(author)
            return author

    async def _authorize(
        self,
        principal: ClaimsIdentity,
        agent: ClaimsIdentity,
    ) -> None:
        if (
            await self._almighty_local_cli_permission.evaluate(agent=agent)
            or await self._almighty_tests_permission.evaluate(agent=agent)
            or await self._edit_authors_permission.evaluate(principal=principal)
        ):
            return
        raise AuthorizationError


class UpdateAuthorCommand:
    def __init__(
        self,
        author_repository: AuthorRepository,
        session: AsyncSession,
    ) -> None:
        self._author_repository = author_repository
        self._session = session

    async def execute(
        self,
        author_id: AuthorId,
        new_name: str,
        *,
        principal: ClaimsIdentity,
        agent: ClaimsIdentity,
    ) -> Author:
        await self._authorize(principal=principal, agent=agent)
        async with self._session.begin():
            author = await self._author_repository.get(author_id)
            author.set_name(new_name)
            await self._author_repository.save(author)
            return author

    async def _authorize(
        self,
        principal: ClaimsIdentity,
        agent: ClaimsIdentity,
    ) -> None:
        agent_name_claim = agent.find_first(AgentNameClaim)
        if agent_name_claim and agent_name_claim.agent_name in (
            AGENT_NAME_LOCAL_CLI,
            AGENT_NAME_TESTS,
        ):
            return

        role_claims = principal.find_all(PisakaRoleClaim)
        if any(role_claim.role == PisakaRole.CHIEF for role_claim in role_claims):
            return

        raise AuthorizationError


class DeleteAuthorCommand:
    def __init__(
        self,
        author_repository: AuthorRepository,
        session: AsyncSession,
    ) -> None:
        self._author_repository = author_repository
        self._session = session

    async def execute(self, author_id: AuthorId) -> None:
        async with self._session.begin():
            await self._author_repository.delete(author_id=author_id)


class SetDefaultAuthorCommand:
    def __init__(
        self,
        default_author_service: DefaultAuthorService,
        session: AsyncSession,
    ) -> None:
        self._default_author_service = default_author_service
        self._session = session

    async def execute(self, user_id: UUID, author_id: AuthorId) -> None:
        async with self._session.begin():
            await self._default_author_service.set(user_id=user_id, author_id=author_id)


class ResetDefaultAuthorCommand:
    def __init__(
        self,
        default_author_service: DefaultAuthorService,
        session: AsyncSession,
    ) -> None:
        self._default_author_service = default_author_service
        self._session = session

    async def execute(self, user_id: UUID) -> None:
        async with self._session.begin():
            await self._default_author_service.reset(user_id=user_id)
