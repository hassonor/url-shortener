import logging
from typing import Optional

import asyncpg
from asyncpg import UniqueViolationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from infrastructure.config import settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.pool = None

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(asyncpg.InterfaceError),
    )
    async def connect(self):
        """
        Attempt to connect to Postgres with retries on transient errors.
        """
        try:
            self.pool = await asyncpg.create_pool(
                user=settings.PG_USER,
                password=settings.PG_PASSWORD,
                database=settings.PG_DATABASE,
                host=settings.PG_HOST,
                port=settings.PG_PORT,
                min_size=1,
                max_size=5,
            )
            logger.debug("PostgreSQL pool created, proceeding to init_db.")
            await self.init_db()

            # Optionally, run a quick test query to ensure DB is ready
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            logger.info("Connected to PostgreSQL and verified connection.")
        except asyncpg.PostgresError as e:
            # If we reach here, it might be a non-transient error or retried out
            logger.error("Failed to connect to Postgres after retries: %s", e)
            raise

    async def init_db(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS url_mappings (
            id SERIAL PRIMARY KEY,
            short_code VARCHAR(20) UNIQUE NOT NULL,
            long_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        logger.debug("Initializing database schema if not present.")
        async with self.pool.acquire() as conn:
            await conn.execute(create_table_query)
            logger.info("Database schema ensured (url_mappings table present).")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(asyncpg.InterfaceError),
    )
    async def insert_url_mapping(self, short_code: str, long_url: str) -> None:
        """
        Insert a new URL mapping. On UniqueViolationError (not transient), do not retry.
        On other transient interface errors, retry a few times.
        """
        insert_query = """
        INSERT INTO url_mappings (short_code, long_url) VALUES ($1, $2)
        ON CONFLICT DO NOTHING;
        """
        logger.debug("Attempting to insert short_code=%s, long_url=%s", short_code, long_url)
        async with self.pool.acquire() as conn:
            try:
                result = await conn.execute(insert_query, short_code, long_url)
                # result typically "INSERT 0 1" or "INSERT 0 0"
                if result.endswith("0 1"):
                    logger.info(
                        "Inserted new mapping short_code=%s long_url=%s",
                        short_code,
                        long_url,
                    )
                else:
                    logger.info("No insert performed, short_code=%s already exists.", short_code)
            except UniqueViolationError:
                # This is expected if the short_code already exists
                logger.info("Short code %s already exists, no insert needed.", short_code)
            except asyncpg.PostgresError as e:
                # Possibly transient if interface related, else permanent
                logger.warning(
                    "Transient Postgres error on insert short_code=%s long_url=%s, will retry: %s",
                    short_code,
                    long_url,
                    e,
                )
                raise  # trigger tenacity retry

    async def get_long_url(self, short_code: str) -> Optional[str]:
        logger.debug("Fetching long_url for short_code=%s", short_code)
        select_query = "SELECT long_url FROM url_mappings WHERE short_code = $1;"
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(select_query, short_code)
            if result:
                logger.debug("Found long_url for short_code=%s", short_code)
                return result["long_url"]
            logger.debug("No long_url found for short_code=%s", short_code)
            return None

    async def get_short_code_by_long_url(self, long_url: str) -> Optional[str]:
        logger.debug("Fetching short_code for long_url=%s", long_url)
        query = "SELECT short_code FROM url_mappings WHERE long_url = $1;"
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, long_url)
            if result:
                logger.debug("Found short_code for long_url=%s", long_url)
                return result["short_code"]
            logger.debug("No short_code found for long_url=%s", long_url)
            return None

    async def close(self):
        if self.pool:
            logger.debug("Closing PostgreSQL pool.")
            await self.pool.close()
            logger.info("PostgreSQL pool closed.")


database = Database()
