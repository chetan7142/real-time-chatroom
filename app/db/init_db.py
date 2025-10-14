import asyncio
from app.db.session import engine
from app.db.base import Base
import app.models.user as user_model
import app.models.room as room_model
import app.models.message as message_model

async def init_models():
    async with engine.begin() as conn:
        # Drop all tables? Be careful in prod. Here we create if not exists.
        await conn.run_sync(Base.metadata.create_all)

if __name__ == '__main__':
    asyncio.run(init_models())
