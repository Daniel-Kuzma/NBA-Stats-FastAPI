from fastapi import APIRouter, Request, Path
from core.limiter import limiter
from database.core import db_dependency
from auth.service import user_dependency
from starlette import status
from .service import *
from .schemas import *

router = APIRouter()

@router.post("/add-favorite-player/{display_name}", response_model = SuccessfullyMessageRespond, status_code = status.HTTP_201_CREATED)
@limiter.limit("200/minute")
async def add_favorite_player(db : db_dependency, user : user_dependency, request : Request, display_name : str = Path(description = "Pass full player name and last name")):
    return await add_user_favorite_player(display_name, db , user)

@router.delete("/delete-favorite-player/{display_name}", response_model = SuccessfullyMessageRespond, status_code = status.HTTP_200_OK)
@limiter.limit("200/minute")
async def delete_favorite_player(db : db_dependency, user : user_dependency, request : Request, display_name : str = Path(description = "Pass full player name and last name")):
    return await delete_user_favorite_player(display_name, db, user)

@router.get("/user-favorite-players", response_model = list[AllUserFavoritePlayersResponse], status_code = status.HTTP_200_OK)
@limiter.limit("200/minute")
async def user_favorite_players(db : db_dependency, user : user_dependency, request : Request):
    return await all_user_favorite_players(db, user)

@router.post("/add-favorite-team/{team_name}", response_model = SuccessfullyMessageRespond, status_code = status.HTTP_201_CREATED)
@limiter.limit("200/minute")
async def add_favorite_team(db : db_dependency, user : user_dependency, request : Request, team_name : str = Path(description = "Pass full team name")):
    return await add_user_favorite_team(team_name, db, user)

@router.delete("/delete-favorite-team/{team_name}", response_model = SuccessfullyMessageRespond, status_code = status.HTTP_200_OK)
@limiter.limit("200/minute")
async def delete_favorite_player(request : Request, db : db_dependency, user : user_dependency, team_name : str = Path(description = "Pass full team name")):
    return await delete_user_favorite_team(team_name, db, user)

@router.get("/user-favorite-teams", response_model = list[AllUserFavoriteTeamResponse], status_code = status.HTTP_200_OK)
@limiter.limit("200/minute")
async def user_favorite_teams(db : db_dependency, user : user_dependency, request : Request):
    return await all_user_favorite_team(db, user)

@router.get("/show-team-stats/{team_name}/{season}", response_model = StatsRespons, status_code = status.HTTP_200_OK)
@limiter.limit("200/minute")
async def team_stats(request : Request, db : db_dependency, team_name : str = Path(description = "Pass full team name"), season : str = Path(description = "Specify the season for which you want statistics.", json_schema_extra={"example": "2025-26"})):
    return await all_team_stats(team_name, season, db)

@router.get("/show-player-stats/{display_name}/{season}", response_model = StatsRespons, status_code = status.HTTP_200_OK)
@limiter.limit("200/minute")
async def player_stats(request : Request, db : db_dependency, display_name : str = Path(description = "Pass full player name and last name"), season : str = Path(description = "Specify the season for which you want statistics.", json_schema_extra={"example": "2025-26"})):
    return await all_player_stats(display_name, season, db)

@router.get("/show-team-stats_against_team/{team_name}/{against_team}/{season}", response_model = StatsRespons, status_code = status.HTTP_200_OK)
@limiter.limit("200/minute")
async def team_stats_against(request : Request, db : db_dependency, team_name : str = Path(description = "Pass full team name"), against_team : str = Path(description = "Pass full team name"), season : str = Path(description = "Specify the season for which you want statistics.", json_schema_extra={"example": "2025-26"})):
    return await compare_team_to_team(team_name, against_team, season, db)

@router.get("/show-player-stats-against-team/{display_name}/{against_team}/{season}", response_model = PlayerStatsRespons, status_code = status.HTTP_200_OK)
@limiter.limit("200/minute")
async def player_stats(request : Request, db : db_dependency, display_name : str = Path(description = "Pass full player name and last name"), against_team : str = Path(description = "Pass full team name"), season : str = Path(description = "Specify the season for which you want statistics.", json_schema_extra={"example": "2025-26"})):
    return await compare_player_to_team(display_name, against_team, season, db)