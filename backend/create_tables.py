import asyncio
from app.db.session import engine, Base

# Import all models
from app.models.models import *

async def create_tables():
    print("Creating tables in Neon...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All tables created successfully in Neon!")

if __name__ == "__main__":
    asyncio.run(create_tables()) 
