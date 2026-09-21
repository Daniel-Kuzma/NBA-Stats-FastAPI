from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from settings import settings

SQL_ALCHEMY_DATABASE_URL = settings.database_url

engine = create_async_engine(SQL_ALCHEMY_DATABASE_URL, connect_args = {"server_settings" : {"timezone" : "Europe/Warsaw"}})

LocalSession = async_sessionmaker(autocommit = False, bind = engine, expire_on_commit = False)
