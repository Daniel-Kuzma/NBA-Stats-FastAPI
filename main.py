from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from typing import Annotated
from database import LocalSession

app = FastAPI()

@app.get("/", status_code = status.HTTP_200_OK)
async def healthy_check():
    return {"healthy_check" : "Welcome"}
