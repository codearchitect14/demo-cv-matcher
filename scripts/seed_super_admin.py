import os
import sys
import asyncio
import asyncpg
import bcrypt


EMAIL = os.getenv("SUPER_ADMIN_EMAIL", "superadmin@boolmind.com")
PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "ChangeMe!123")
FULL_NAME = os.getenv("SUPER_ADMIN_NAME", "Super Admin")


async def main() -> None:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL env var is required")
    if dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)

    # Hash password with bcrypt
    hashed = bcrypt.hashpw(PASSWORD.encode("utf-8"), bcrypt.gensalt(rounds=int(os.getenv("BCRYPT_ROUNDS", "10")))).decode("utf-8")

    conn = await asyncpg.connect(dsn, statement_cache_size=0, command_timeout=10)
    try:
        # Upsert by email
        row = await conn.fetchrow(
            """
            INSERT INTO super_admins (email, password_hash, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (email) DO UPDATE SET
              password_hash = EXCLUDED.password_hash,
              full_name = EXCLUDED.full_name,
              is_active = true,
              updated_at = now()
            RETURNING id::text as id, email, full_name, is_active
            """,
            EMAIL.lower().strip(), hashed, FULL_NAME,
        )
        print({"created_or_updated": True, "id": row["id"], "email": row["email"], "is_active": row["is_active"]})
    finally:
        await conn.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Seeding failed: {e}", file=sys.stderr)
        sys.exit(1)


