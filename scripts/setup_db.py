"""
Run this script to initialize the database with migrations and seed data.
Usage: python scripts/setup_db.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


async def main():
    print("[NEXUS] Initializing database...")
    from app.database import init_db, engine, AsyncSessionLocal
    from app.models import User, Region
    # Touch additional models so SQLAlchemy registers all tables
    from app.models import organization as _org  # noqa: F401
    from app.models import scan as _scan          # noqa: F401
    from app.models import anomaly as _anom       # noqa: F401
    from app.models import report as _rep         # noqa: F401
    from app.utils.auth import hash_password
    from sqlalchemy import select

    await init_db()
    print("[NEXUS] Tables created.")

    async with AsyncSessionLocal() as db:
        # Create default admin user
        result = await db.execute(select(User).where(User.email == "admin@nexus.local"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin@nexus.local",
                username="NEXUS-ADMIN",
                hashed_password=hash_password("nexus2024"),
                full_name="System Administrator",
                role="admin",
            )
            db.add(admin)
            print("[NEXUS] Default admin created: admin@nexus.local / nexus2024")

        # Seed regions if empty
        count = await db.scalar(__import__("sqlalchemy").select(__import__("sqlalchemy").func.count()).select_from(Region))
        if not count:
            regions = [
                Region(name="Amazon Basin", description="Deforestation monitoring", category="forest",
                       lat_min=-10, lat_max=0, lon_min=-65, lon_max=-50, watch_level="high"),
                Region(name="Arctic Ice Edge", description="Seasonal ice coverage", category="arctic",
                       lat_min=70, lat_max=80, lon_min=-30, lon_max=30, watch_level="normal"),
                Region(name="Sahara Front", description="Desertification boundary", category="desert",
                       lat_min=12, lat_max=20, lon_min=-5, lon_max=20, watch_level="medium"),
                Region(name="South China Sea", description="Maritime monitoring", category="ocean",
                       lat_min=10, lat_max=22, lon_min=110, lon_max=125, watch_level="high"),
            ]
            for r in regions:
                db.add(r)
            print(f"[NEXUS] {len(regions)} regions seeded.")

        await db.commit()

    print("[NEXUS] Database ready.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
