from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

STATEMENT_TIMEOUT_MS = 5_000
IDLE_IN_TRANSACTION_TIMEOUT_MS = 10_000


def build_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=10,
        connect_args={
            "server_settings": {
                "statement_timeout": str(STATEMENT_TIMEOUT_MS),
                # Anything slow, an LLM call above all, has to happen outside a transaction, or
                # Postgres ends the connection here. See issue H9.
                "idle_in_transaction_session_timeout": str(IDLE_IN_TRANSACTION_TIMEOUT_MS),
                "application_name": "samvid-api",
            }
        },
    )


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
