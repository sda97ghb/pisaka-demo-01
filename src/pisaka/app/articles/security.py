from pisaka.app.articles.entities import ArticleDraft
from pisaka.platform.security.claims import ClaimsIdentity
from pisaka.platform.security.roles import PisakaRole
from pisaka.platform.security.utils import get_user_id, has_any_role, has_role

ROLES_ALLOWED_TO_EDIT_ARTICLE_DRAFTS = [
    PisakaRole.JOURNALIST,
    PisakaRole.EDITOR,
    PisakaRole.CHIEF,
]


class ListArticleDraftsPermission:
    async def evaluate(self, principal: ClaimsIdentity) -> bool:
        return has_any_role(
            principal=principal,
            roles=ROLES_ALLOWED_TO_EDIT_ARTICLE_DRAFTS,
        )


class PublishArticlePermission:
    async def evaluate(
        self,
        principal: ClaimsIdentity,
        article_draft: ArticleDraft,
    ) -> bool:
        if has_role(principal, PisakaRole.CHIEF):
            return True
        if has_role(principal, PisakaRole.EDITOR):
            user_id = get_user_id(principal)
            if article_draft.is_editor(user_id):
                return True
        return False
