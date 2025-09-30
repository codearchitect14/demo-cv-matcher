import asyncio
import os
import pathlib
import sys

import asyncpg


SQL_PATH = pathlib.Path(__file__).parent / "create_super_admins_table.sql"


async def main() -> None:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL env var is required")
    if dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)

    sql = SQL_PATH.read_text(encoding="utf-8")

    conn = await asyncpg.connect(dsn, statement_cache_size=0, command_timeout=15)
    try:
        # Ensure functions available for uuid default if used
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        await conn.execute(sql)
        print("✅ super_admins table migration applied.")
    finally:
        await conn.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        sys.exit(1)


