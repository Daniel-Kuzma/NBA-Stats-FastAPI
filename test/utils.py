import pytest_asyncio
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from main import app
from fastapi.testclient import TestClient
import pytest
import models
from routes.auth import bcrypt_context, get_current_user
from database import get_db
from datetime import datetime
import uuid

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def override_get_db():
    async with TestingSessionLocal() as db:
        yield db

def override_get_current_user():
    return {"username": "jan123", "id": "07c206d2-3449-451a-9cd7-86a10f6ec18f", "role": "admin"}

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user 

client = TestClient(app)

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)

@pytest_asyncio.fixture
async def test_data_users():
    user = models.Users(
    name = "Jan",
    last_name = "Kowalski",
    username = "jan123",
    password = bcrypt_context.hash("password"),
    email = "jan@jan.pl",
    role = "admin",
    user_status = True,
    public_id = uuid.UUID("07c206d2-3449-451a-9cd7-86a10f6ec18f")
    )
    async with TestingSessionLocal() as db:
        db.add(user)
        await db.commit()
        await db.refresh(user) 
        yield user

@pytest_asyncio.fixture
async def test_data_teams():
    team = models.Teams(
        team_id = 1,
        team_name = "Huston Rockets",
        abbreviation = "HOU"
    )
    team_2 = models.Teams(
        team_id = 2,
        team_name = "Los Angeles Lakers",
        abbreviation = "LAL"
    )
    team_3 = models.Teams(
        team_id = 3,
        team_name = "Cleveland Cavaliers",
        abbreviation = "CLE"
    )
    team_list = [team, team_2, team_3]
    async with TestingSessionLocal() as db:
        db.add_all(team_list)
        await db.commit()
        await db.refresh(team) 
        yield team

@pytest_asyncio.fixture
async def test_data_players():
    player = models.Players(
        player_id = 1,
        player_name = "Kevin",
        player_last_name = "Durant",
        display_name = "Kevin Durant",
        player_team = 1,
        is_active = True
    )
    player_2 = models.Players(
        player_id = 2,
        player_name = "James",
        player_last_name = "Lebron",
        display_name = "James Lebron",
        player_team = 2,
        is_active = True
    )
    player_list = [player, player_2]
    async with TestingSessionLocal() as db:
        db.add_all(player_list)
        await db.commit()
        await db.refresh(player) 
        yield player

@pytest_asyncio.fixture
async def test_data_favorite_player():
    favorite_player = models.UserFavoritePlayer(
        user_id = 1,
        player_id = 1
    )
    async with TestingSessionLocal() as db:
        db.add(favorite_player)
        await db.commit()
        await db.refresh(favorite_player) 
        yield favorite_player

@pytest_asyncio.fixture
async def test_data_favorite_team():
    favorite_team = models.UserFavoriteTeam(
        user_id = 1,
        team_id = 1
    )
    async with TestingSessionLocal() as db:
        db.add(favorite_team)
        await db.commit()
        await db.refresh(favorite_team)
        yield favorite_team

@pytest_asyncio.fixture
async def test_data_player_logs():
    player_game_log = models.PlayersGameLogs(
        season = "2025-26",
        player_id = 1,
        team_id = 1,
        game_id = "00234",
        game_date = datetime(2025, 3, 9),
        matchup = "HOU vs. LAL",
        is_win = True,
        minutes_played = 30,
        field_goals_made = 15,
        field_goals_attempted = 20,
        field_goal_percentage = 80,
        three_point_field_goals_made = 2,
        three_point_field_goals_attempted = 4,
        three_point_field_goal_percentage = 50,
        free_throws_made = 4,
        free_throws_attempted = 4,
        free_throw_percentage = 100,
        offensive_rebounds = 5,
        defensive_rebounds = 3,
        rebounds = 8,
        assists = 3,
        turnovers = 2,
        steals = 1,
        blocks = 3,
        blocks_against =  2,
        personal_fouls = 1,
        personal_fouls_drawn = 1,
        points = 34
    )
    async with TestingSessionLocal() as db:
        db.add(player_game_log)
        await db.commit()
        await db.refresh(player_game_log)
        yield player_game_log

@pytest_asyncio.fixture
async def test_data_team_logs():
    team_game_log = models.TeamsGameLogs(
        season = "2025-26",
        team_id = 1,
        game_id = "00234",
        game_date = datetime(2025, 3, 9),
        matchup = "HOU vs. LAL",
        is_win = True,
        field_goals_made = 40,
        field_goals_attempted = 50,
        field_goal_percentage = 80,
        three_point_field_goals_made = 5,
        three_point_field_goals_attempted = 10,
        three_point_field_goal_percentage = 50,
        free_throws_made = 10,
        free_throws_attempted = 15,
        free_throw_percentage = 67,
        offensive_rebounds = 10,
        defensive_rebounds = 15,
        rebounds = 25,
        assists =  20,
        turnovers = 10,
        steals = 5,
        blocks = 5,
        blocks_against = 6,
        personal_fouls = 12,
        personal_fouls_drawn = 14,
        points = 120
    )
    async with TestingSessionLocal() as db:
        db.add(team_game_log)
        await db.commit()
        await db.refresh(team_game_log)
        yield team_game_log

@pytest_asyncio.fixture
async def test_data_logs():
    logs = models.StatusTLog(
        log_description = "Added some team logs",
        downloaded_records = 1,
        date = datetime(2025, 3, 9),
        completed = True,
        log_type = "teams_log"
    )
    async with TestingSessionLocal() as db:
        db.add(logs)
        await db.commit()
        await db.refresh(logs)
        yield logs


