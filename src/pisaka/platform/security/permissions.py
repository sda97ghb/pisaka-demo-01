from pisaka.platform.security.claims import (
    AGENT_NAME_LOCAL_CLI,
    AGENT_NAME_TESTS,
    ISSUER_LOCAL_AUTHORITY,
    AgentNameClaim,
    ClaimsIdentity,
)

# Привилегии и авторизация это немного разные понятия. Привилегия задает правило,
# у кого какие есть права. Авторизация принимает окончательное решение, разрешить
# доступ или нет. При необходимости авторизация может проверить несколько привилегий
# (не все из них обязаны вернуть True).
#
# Permission.evaluate: (principal, agent, resource, resource_scope, context) -> Has | HasNot | CanNotAnswer
# Authorization.evaluate: (principal, agent, resource, resource_scope, context) -> Allow | Deny
#
# В общем случае они оба принимают аргументы:
# - принципал - от чьего имени выполняются действие
# - агент - кто выполняет действие
# - ресурс - над чем выполняются действие
# - resource scope - при необходимости можно разрешить не полный доступ к ресурсу,
#   а только к части его атрибутов или к ограниченному набору действий с этим ресурсом
#   Соответственно здесь указывается часть или действие
# - context - любая вспомогательная информация, например текущие дата, время
#
# Если какие-то аргументы для вычисления конкретной привилегии не нужны,
# то она их может не принимать. Привилегии НЕ обязаны реализовывать какой-либо
# одинаковый обобщенный интерфейс
#
# Привилегия должна вернуть результат на выбор: есть право, нет права, не могу ответить.
# На практике это удобно сделать как тип возвращаемого значение bool | None
#
# Авторизация должна вернуть результат на выбор: разрешить доступ или запретить.
# На практике удобно для разрешения возвращать None, для запрета делать
# raise AuthorizationError


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
