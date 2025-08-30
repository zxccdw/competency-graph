from fastapi import APIRouter
from dao.comments import CommentsDAO
from models.comments import Comment
from datetime import datetime

router = APIRouter()

@router.post("/comments", response_model=list[Comment])
async def create_comments(
    data: list[Comment]
):
    comments = []
    for comment_data in data:
        comment = await CommentsDAO.create(
            filename=comment_data.filename,
            start_index=comment_data.start_index,
            end_index=comment_data.end_index,
            subject=comment_data.subject,
            predicate=comment_data.predicate,
            object_=comment_data.object,
            author=comment_data.author,
            created_at=comment_data.created_at
        )
        comments.append(Comment.model_validate(comment))
    return comments

@router.get("/comments/{filename}", response_model=list[Comment])
async def get_comments(
    filename: str,
    limit: int = 20
):
    """Получает список комментариев для указанного файла"""
    comments = await CommentsDAO.get_by_filename(filename, limit)
    return [Comment.model_validate(c) for c in comments]
