from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from typing import Annotated
from database.core import LocalSession

from auth.controller import router as auth_router
from user.controller import router as user_router
from admin.controller import router as admin_router
from players.controller import router as players_router

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from core.seeder import upload_new_player_logs, upload_new_teams_logs, check_active_players
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import _rate_limit_exceeded_handler
from core.limiter import limiter


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
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/", status_code = status.HTTP_200_OK)
async def healthy_check():
    return {"healthy_check" : "Welcome"}

app.include_router(admin_router, prefix = "/admin", tags=["admin"])
app.include_router(auth_router)
app.include_router(user_router, prefix = "/account", tags = ["user-account"])
app.include_router(players_router, prefix = "/user", tags = ["user"])