import typing as tp
import asyncpg
import dependency_injector.wiring as wiring
from datetime import datetime


class NodeVersionDB(tp.TypedDict):
    node_uri: str
    version: int
    last_modified: datetime


class NodeChangeDB(tp.TypedDict):
    id: int
    node_uri: str
    user_id: int
    change_type: str
    old_value: tp.Optional[dict]
    new_value: tp.Optional[dict]
    version: int
    changed_at: datetime


class NodeVersionDAO:
    """Data Access Object для работы с версиями узлов"""

    @classmethod
    async def get_version(
        cls,
        node_uri: str,
        db_pool: asyncpg.Pool = wiring.Provide["db_pool"],
    ) -> tp.Optional[NodeVersionDB]:
        """Получить текущую версию узла"""
        version = await db_pool.fetchrow(
            """
            SELECT node_uri, version, last_modified
            FROM node_version
            WHERE node_uri = $1
            """,
            node_uri,
        )
        return tp.cast(NodeVersionDB, dict(version)) if version else None

    @classmethod
    async def increment_version(
        cls,
        node_uri: str,
        current_version: int,
        db_pool: asyncpg.Pool = wiring.Provide["db_pool"],
    ) -> bool:
        """
        Увеличить версию узла.
        Возвращает True если версия успешно обновлена, False если версия не совпадает.
        """
        version = await db_pool.fetchrow(
            """
            UPDATE node_version
            SET version = version + 1,
                last_modified = CURRENT_TIMESTAMP
            WHERE node_uri = $1 AND version = $2
            RETURNING version
            """,
            node_uri,
            current_version,
        )
        return version is not None

    @classmethod
    async def add_change(
        cls,
        node_uri: str,
        user_id: int,
        change_type: str,
        old_value: tp.Optional[dict],
        new_value: tp.Optional[dict],
        version: int,
        db_pool: asyncpg.Pool = wiring.Provide["db_pool"],
    ) -> NodeChangeDB:
        """Добавить запись об изменении узла"""
        change = await db_pool.fetchrow(
            """
            INSERT INTO node_change_history (
                node_uri, user_id, change_type,
                old_value, new_value, version
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            """,
            node_uri, user_id, change_type,
            old_value, new_value, version,
        )
        return tp.cast(NodeChangeDB, dict(change))

    @classmethod
    async def get_changes(
        cls,
        node_uri: str,
        db_pool: asyncpg.Pool = wiring.Provide["db_pool"],
    ) -> tp.List[NodeChangeDB]:
        """Получить историю изменений узла"""
        changes = await db_pool.fetch(
            """
            SELECT *
            FROM node_change_history
            WHERE node_uri = $1
            ORDER BY changed_at DESC
            """,
            node_uri,
        )
        return [tp.cast(NodeChangeDB, dict(change)) for change in changes]
