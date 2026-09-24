from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from typing import Annotated
from database import LocalSession
from routes import admin, auth
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from seeder import upload_new_player_logs, upload_new_teams_logs, check_active_players


async def upload_teams_logs():
    async with LocalSession() as db:
        await upload_new_teams_logs(db = db)

async def upload_players_logs():
    async with LocalSession() as db:
        await upload_new_player_logs(db = db)

async def update_active_players():
    async with LocalSession() as db:
        await check_active_players(db = db)

@asynccontextmanager
async def lifespan(app : FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(upload_teams_logs, "interval", hours = 1, misfire_grace_time=600, coalesce=True)
    scheduler.add_job(upload_players_logs, "interval", hours = 1, misfire_grace_time=600, coalesce=True)
    scheduler.add_job(update_active_players, "cron", hour = 2, misfire_grace_time=600, coalesce=True)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan = lifespan)

@app.get("/", status_code = status.HTTP_200_OK)
async def healthy_check():
    return {"healthy_check" : "Welcome"}

app.include_router(admin.router)
app.include_router(auth.router)