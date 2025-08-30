import asyncpg
import typing as tp
from datetime import datetime
import dependency_injector.wiring as wiring

class CommentDB(tp.TypedDict):
    id: int
    filename: str
    start_index: int
    end_index: int
    subject: str
    predicate: str
    object: str
    created_at: datetime
    author: str

class CommentsDAO:
    @classmethod
    async def create(
        cls,
        filename: str,
        start_index: int,
        end_index: int,
        subject: str,
        predicate: str,
        object_: str,
        author: str,
        created_at: tp.Optional[datetime] = None,
        db_pool: asyncpg.Pool = wiring.Provide["db_pool"]
    ) -> CommentDB:
        """Создает новый комментарий в базе данных"""
        row = await db_pool.fetchrow(
            """
            INSERT INTO comments (filename, start_index, end_index, subject, predicate, object, author, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, filename, start_index, end_index, subject, predicate, object, created_at, author
            """,
            filename,
            start_index,
            end_index,
            subject,
            predicate,
            object_,
            author,
            created_at or datetime.now().astimezone()
        )
        return tp.cast(CommentDB, dict(row))

    @classmethod
    async def get_by_filename(
        cls,
        filename: str,
        limit: int = 500,
        db_pool: asyncpg.Pool = wiring.Provide["db_pool"]
    ) -> list[CommentDB]:
        """Получает список комментариев для указанного файла"""
        rows = await db_pool.fetch(
            """
            SELECT
                id,
                filename,
                start_index,
                end_index,
                subject,
                predicate,
                object,
                created_at,
                author
            FROM comments
            WHERE filename = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            filename,
            limit
        )
        return [tp.cast(CommentDB, dict(row)) for row in rows]
