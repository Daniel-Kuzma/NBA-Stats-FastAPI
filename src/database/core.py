from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.settings import settings
from typing import Annotated
from fastapi import Depends

SQL_ALCHEMY_DATABASE_URL = settings.database_url

engine = create_async_engine(SQL_ALCHEMY_DATABASE_URL, connect_args = {"server_settings" : {"timezone" : "Europe/Warsaw"}})

LocalSession = async_sessionmaker(autocommit = False, bind = engine, expire_on_commit = False)

async def get_db():
    async with LocalSession() as db:
        yield db

db_dependency = Annotated[AsyncSession, Depends(get_db)]