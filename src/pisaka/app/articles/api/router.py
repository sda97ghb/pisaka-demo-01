from fastapi import APIRouter

from . import article_drafts, articles

router = APIRouter()
router.include_router(articles.router)
router.include_router(article_drafts.router)
