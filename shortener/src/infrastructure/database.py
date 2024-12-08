import logging
from typing import Optional
import asyncpg
from infrastructure.config import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user=settings.PG_USER,
            password=settings.PG_PASSWORD,
            database=settings.PG_DATABASE,
            host=settings.PG_HOST,
            port=settings.PG_PORT,
            min_size=1,
            max_size=5
        )
        await self.init_db()
        logger.info("Connected to PostgreSQL.")

    async def init_db(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS url_mappings (
            id SERIAL PRIMARY KEY,
            short_code VARCHAR(20) UNIQUE NOT NULL,
            long_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        async with self.pool.acquire() as conn:
            await conn.execute(create_table_query)
            logger.info("Database schema ensured.")

    async def insert_url_mapping(self, short_code: str, long_url: str) -> None:
        insert_query = """
        INSERT INTO url_mappings (short_code, long_url) VALUES ($1, $2)
        ON CONFLICT DO NOTHING;
        """
        async with self.pool.acquire() as conn:
            await conn.execute(insert_query, short_code, long_url)

    async def get_long_url(self, short_code: str) -> Optional[str]:
        select_query = "SELECT long_url FROM url_mappings WHERE short_code = $1;"
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(select_query, short_code)
            if result:
                return result["long_url"]
            return None

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL pool closed.")

database = Database()
