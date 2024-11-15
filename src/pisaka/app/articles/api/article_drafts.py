from fastapi import APIRouter

router = APIRouter(
    prefix="/article-drafts",
    tags=["Статьи"],
)
