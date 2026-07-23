"""Seed the default admin user into PostgreSQL.

Usage: python -m app.seeds.admin
"""
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import Base, get_engine, get_session_factory
from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.models import AdminUser

configure_logging()
logger = get_logger("seed_admin")


async def seed_admin_user(session: AsyncSession) -> None:
    """Create or update default admin user."""
    settings = get_settings()

    # Check if admin exists
    stmt = select(AdminUser).where(AdminUser.username == settings.admin_username)
    existing = await session.scalar(stmt)

    if existing:
        logger.info(f"admin user '{settings.admin_username}' already exists, skipping")
        return

    # Create new admin
    admin = AdminUser(
        username=settings.admin_username,
        password_hash=hash_password(settings.admin_password),
        is_active=True,
    )
    session.add(admin)
    await session.commit()
    logger.info(f"created admin user: {settings.admin_username}")


async def main() -> None:
    """Entry point."""
    engine = get_engine()
    factory = get_session_factory()

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("tables created/verified")

    # Seed admin
    async with factory() as session:
        await seed_admin_user(session)

    await engine.dispose()
    logger.info("seed complete")


if __name__ == "__main__":
    asyncio.run(main())
