import typing as tp
import asyncpg
import dependency_injector.wiring as wiring


class UserDescriptor(tp.TypedDict):
    display_name: str
    email: str


class UserDB(tp.TypedDict):
    id: int
    display_name: str
    email: str


class UserDAO:
    """Data Access Object для работы с пользователями"""

    @classmethod
    async def get_or_create(
        cls,
        user: UserDescriptor,
        db_pool: asyncpg.Pool = wiring.Provide["db_pool"],
    ) -> UserDB:
        """Получить или создать пользователя"""
        await db_pool.execute(
            """
            INSERT INTO "user" (display_name, email)
            VALUES ($1, $2)
            ON CONFLICT (email) DO UPDATE SET display_name = EXCLUDED.display_name
            """,
            user["display_name"],
            user["email"],
        )

        user = await db_pool.fetchrow(
            """
            SELECT id, display_name, email
            FROM "user"
            WHERE email = $1
            """,
            user["email"],
        )

        return tp.cast(UserDB, dict(user))

    @classmethod
    async def get_by_email(
        cls,
        email: str,
        db_pool: asyncpg.Pool = wiring.Provide["db_pool"],
    ) -> tp.Optional[UserDB]:
        """Получить пользователя по email"""
        user = await db_pool.fetchrow(
            """
            SELECT id, display_name, email
            FROM "user"
            WHERE email = $1
            """,
            email,
        )

        return tp.cast(UserDB, dict(user)) if user else None

    @classmethod
    async def get_by_competency(
        cls,
        competency_id: str,
        db_pool: asyncpg.Pool = wiring.Provide["db_pool"],
    ) -> tp.List[UserDB]:
        """Получить пользователей, связанных с компетенцией"""
        users = await db_pool.fetch(
            """
            SELECT u.id, u.display_name, u.email
            FROM "user" u
            JOIN user_competency uc ON u.id = uc.user_id
            WHERE uc.competency_id = $1
            """,
            competency_id,
        )

        return [tp.cast(UserDB, dict(user)) for user in users]
