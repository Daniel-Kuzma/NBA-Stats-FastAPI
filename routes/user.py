from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, Numeric, cast
from typing import Annotated
from starlette import status
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
from routes.auth import get_current_user
from models import UserFavoritePlayer, UserFavoriteTeam, Players, Teams, TeamsGameLogs, PlayersGameLogs
from seeder import get_actual_season, get_season_years_list
from database import get_db

db_dependency = Annotated[AsyncSession, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

router = APIRouter()

@router.post("/add-favorite-player/{display_name}", status_code = status.HTTP_201_CREATED)
async def add_favorite_player(db : db_dependency, user : user_dependency, display_name : str = Path(description = "Pass full player name and last name")):
    
    stmt_player_id = await db.execute(select(Players.player_id).where(Players.display_name == display_name).limit(1))
    result_player_id = stmt_player_id.scalar()
    if result_player_id is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Player is not exists")
    
    stmt_check_user_favorite_players = await db.execute(select(UserFavoritePlayer).where(UserFavoritePlayer.player_id == result_player_id, UserFavoritePlayer.user_id == user.get("id")).limit(1))
    check = stmt_check_user_favorite_players.scalar()
    if check is not None:
        raise HTTPException(status_code = status.HTTP_406_NOT_ACCEPTABLE, detail = "This player is already added into your favorite players")
    try:
        new_favorite_player = UserFavoritePlayer(user_id = user.get("id"), player_id = result_player_id)
        db.add(new_favorite_player)
        await db.commit()
        return {"detail" : "Successfully added new favorite player"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error: {e}")

@router.delete("/delete-favorite-player/{display_name}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_favorite_player(db : db_dependency, user : user_dependency, display_name : str = Path(description = "Pass full player name and last name")):
    
    stmt_player_id = await db.execute(select(Players.player_id).where(Players.display_name == display_name).limit(1))
    result_player_id = stmt_player_id.scalar()
    if result_player_id is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Player is not exists")
    
    stmt_check_user_favorite_players = await db.execute(select(UserFavoritePlayer).where(UserFavoritePlayer.player_id == result_player_id, UserFavoritePlayer.user_id == user.get("id")).limit(1))
    check = stmt_check_user_favorite_players.scalar()
    if check is None:
        raise HTTPException(status_code = status.HTTP_406_NOT_ACCEPTABLE, detail = "This player is not added into your favorite players")
    
    try:
        await db.execute(delete(UserFavoritePlayer).where(UserFavoritePlayer.user_id == user.get("id"), UserFavoritePlayer.player_id == result_player_id))
        await db.commit()
        return {"detail" : "Successfully deleted favorite player"}
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error {e}")

@router.get("/user-favorite-players", status_code = status.HTTP_200_OK)
async def user_favorite_players(db : db_dependency, user : user_dependency):
    try:
        stmt_user_favorite_players = await db.execute(
            select(UserFavoritePlayer.id,
                   Players.display_name,
                   Teams.team_name,
                   func.round(func.avg(PlayersGameLogs.points), 1).label("avg_points"),
                   func.round(func.avg(PlayersGameLogs.assists), 1).label("avg_assist"),
                   func.round(func.avg(PlayersGameLogs.steals), 1).label("avg_steals"))
            .join(Players, UserFavoritePlayer.player_id == Players.player_id)
            .join(Teams, Players.player_team == Teams.team_id)
            .join(PlayersGameLogs, UserFavoritePlayer.player_id == PlayersGameLogs.player_id)
            .where(UserFavoritePlayer.user_id == user.get("id"), PlayersGameLogs.season == get_actual_season())
            .group_by(UserFavoritePlayer.id, Players.display_name, Teams.team_name))
        
        result = stmt_user_favorite_players.mappings().all()
        if not result:
            return {"detail" : "You need to add favorite players"}
        return result
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error : {e}")

@router.post("/add-favorite-team/{team_name}", status_code = status.HTTP_201_CREATED)
async def add_favorite_team(db : db_dependency, user : user_dependency, team_name : str = Path(description = "Pass full team name")):
    
    stmt_team_id = await db.execute(select(Teams.team_id).where(Teams.team_name == team_name).limit(1))
    team_id_result = stmt_team_id.scalar()
    if team_id_result is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Team is not exist")

    stmt_check_user_favorite_teams = await db.execute(select(UserFavoriteTeam).where(UserFavoriteTeam.team_id == team_id_result, UserFavoriteTeam.user_id == user.get("id")).limit(1))
    check = stmt_check_user_favorite_teams.scalar()
    if check is not None:
        raise HTTPException(status_code = status.HTTP_406_NOT_ACCEPTABLE, detail = "This team is already added into your favorite teams")
    
    try:
        new_favorite_team = UserFavoriteTeam(user_id = user.get("id"), team_id = team_id_result)
        db.add(new_favorite_team)
        await db.commit()
        return {"detail" : "Successfully added new favorite team"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error: {e}")

@router.delete("/delete-favorite-team/{team_name}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_favorite_player(db : db_dependency, user : user_dependency, team_name : str = Path(description = "Pass full team name")):

    stmt_team_id = await db.execute(select(Teams.team_id).where(Teams.team_name == team_name).limit(1))
    team_id_result = stmt_team_id.scalar()
    if team_id_result is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Team is not exist")

    stmt_check_user_favorite_teams = await db.execute(select(UserFavoriteTeam).where(UserFavoriteTeam.team_id == team_id_result, UserFavoriteTeam.user_id == user.get("id")).limit(1))
    check = stmt_check_user_favorite_teams.scalar()
    if check is None:
        raise HTTPException(status_code = status.HTTP_406_NOT_ACCEPTABLE, detail = "This team is not added into your favorite teams")

    try:
        await db.execute(delete(UserFavoriteTeam).where(UserFavoriteTeam.user_id == user.get("id"), UserFavoriteTeam.team_id == team_id_result))
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error {e}")

    return {"detail" : "Successfully deleted favorite team"}

@router.get("/user-favorite-teams")
async def user_favorite_teams(db : db_dependency, user : user_dependency):
    try:
        stmt_favorite_teams = await db.execute(
            select(UserFavoriteTeam.id,
                   Teams.team_name,
                   func.round(func.avg(TeamsGameLogs.points), 1).label("avg_points"),
                   func.round(func.avg(TeamsGameLogs.assists), 1).label("avg_assists"),
                   func.round(func.avg(TeamsGameLogs.steals), 1).label("avg_steals"))
            .join(Teams, UserFavoriteTeam.team_id == Teams.team_id)
            .join(TeamsGameLogs, UserFavoriteTeam.team_id == TeamsGameLogs.team_id)
            .where(UserFavoriteTeam.user_id == user.get("id"), TeamsGameLogs.season == get_actual_season())
            .group_by(UserFavoriteTeam.id, Teams.team_name))
        
        result = stmt_favorite_teams.mappings().all()
        if not result:
            return {"detail" : "No favorite teams add yet"}
        return result
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error: {e}")

@router.get("/show-team-stats/{team_name}/{season}", status_code = status.HTTP_200_OK)
async def team_stats(db : db_dependency, team_name : str = Path(description = "Pass full team name"), season : str = Path(description = "Specify the season for which you want statistics.", json_schema_extra={"example": "2025-26"})):
    stmt_team_id = await db.execute(select(Teams.team_id).where(Teams.team_name == team_name).limit(1))
    result_team_id = stmt_team_id.scalar()
    if result_team_id is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Team is not exist")

    if season not in get_season_years_list(2000):
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Season is not exist or will start soon")

    stmt_team_stats = await db.execute(select(func.round(func.avg(TeamsGameLogs.points), 1).label("avg points"),
                                                func.round(func.avg(TeamsGameLogs.assists), 1).label("avg assists"),
                                                func.round(func.avg(TeamsGameLogs.blocks), 1).label("avg blocks"),
                                                func.round(func.avg(TeamsGameLogs.steals), 1).label("avg steals"),
                                                func.round(func.avg(TeamsGameLogs.turnovers), 1).label("avg turnovers"),
                                                func.round(func.avg(TeamsGameLogs.rebounds), 1).label("avg rebounds"),
                                                func.round(func.avg(TeamsGameLogs.offensive_rebounds), 1).label("avg offensive rebounds"),
                                                func.round(func.avg(TeamsGameLogs.defensive_rebounds), 1).label("avg defensive rebounds"),
                                                func.round(func.avg(TeamsGameLogs.personal_fouls), 1).label("avg personal fouls"),
                                                func.round(func.avg(TeamsGameLogs.personal_fouls_drawn), 1).label("avg personal fouls drawn"),
                                                func.round(func.avg(TeamsGameLogs.field_goals_made), 2).label("avg field goals made"),
                                                func.round(func.avg(TeamsGameLogs.field_goals_attempted), 2).label("avg field goals attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.field_goal_percentage), Numeric), 2).label("avg field goal percentage"),
                                                func.round(func.avg(TeamsGameLogs.three_point_field_goals_made), 2).label("avg three point field goals made"),
                                                func.round(func.avg(TeamsGameLogs.three_point_field_goals_attempted), 2).label("avg three point field goals attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.three_point_field_goal_percentage), Numeric), 2).label("avg_three_point_field_goal_percentage"),
                                                func.round(func.avg(TeamsGameLogs.free_throws_made), 2).label("avg free throws made"),
                                                func.round(func.avg(TeamsGameLogs.free_throws_attempted), 2).label("avg free throws attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.free_throw_percentage), Numeric), 2).label("avg free throw percentage")   
                                              ).where(TeamsGameLogs.team_id == result_team_id, TeamsGameLogs.season == season))
    team_stats_result = stmt_team_stats.mappings().first()
    if team_stats_result.get("avg points") == None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Stats not found for this team and season")
    
    return team_stats_result

@router.get("/show-player-stats/{display_name}/{season}", status_code = status.HTTP_200_OK)
async def player_stats(db : db_dependency, display_name : str = Path(description = "Pass full player name and last name"), season : str = Path(description = "Specify the season for which you want statistics.", json_schema_extra={"example": "2025-26"})):
    stmt_player_id = await db.execute(select(Players.player_id).where(Players.display_name == display_name).limit(1))
    result_player_id = stmt_player_id.scalar()
    if result_player_id is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Player is not exist")

    if season not in get_season_years_list(2000):
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Season is not exist or will start soon")

    stmt_player_stats = await db.execute(select(func.round(cast(func.avg(PlayersGameLogs.points), Numeric), 1).label("avg points"),
                                                func.round(func.avg(PlayersGameLogs.assists), 1).label("avg assists"),
                                                func.round(func.avg(PlayersGameLogs.blocks), 1).label("avg blocks"),
                                                func.round(func.avg(PlayersGameLogs.steals), 1).label("avg steals"),
                                                func.round(func.avg(PlayersGameLogs.turnovers), 1).label("avg turnovers"),
                                                func.round(func.avg(PlayersGameLogs.rebounds), 1).label("avg rebounds"),
                                                func.round(func.avg(PlayersGameLogs.offensive_rebounds), 1).label("avg offensive rebounds"),
                                                func.round(func.avg(PlayersGameLogs.defensive_rebounds), 1).label("avg defensive rebounds"),
                                                func.round(func.avg(PlayersGameLogs.personal_fouls), 1).label("avg personal fouls"),
                                                func.round(func.avg(PlayersGameLogs.personal_fouls_drawn), 1).label("avg personal fouls drawn"),
                                                func.round(func.avg(PlayersGameLogs.field_goals_made), 2).label("avg field goals made"),
                                                func.round(func.avg(PlayersGameLogs.field_goals_attempted), 2).label("avg field goals attempted"),
                                                func.round(cast(func.avg(PlayersGameLogs.field_goal_percentage), Numeric), 2).label("avg field goal percentage"),
                                                func.round(func.avg(PlayersGameLogs.three_point_field_goals_made), 2).label("avg three point field goals made"),
                                                func.round(func.avg(PlayersGameLogs.three_point_field_goals_attempted), 2).label("avg three point field goals attempted"),
                                                func.round(cast(func.avg(PlayersGameLogs.three_point_field_goal_percentage), Numeric), 2).label("avg_three_point_field_goal_percentage"),
                                                func.round(func.avg(PlayersGameLogs.free_throws_made), 2).label("avg free throws made"),
                                                func.round(func.avg(PlayersGameLogs.free_throws_attempted), 2).label("avg free throws attempted"),
                                                func.round(cast(func.avg(PlayersGameLogs.free_throw_percentage), Numeric), 2).label("avg free throw percentage")    
                                              ).where(PlayersGameLogs.player_id == result_player_id, PlayersGameLogs.season == season))
    player_stats_result = stmt_player_stats.mappings().first()
    if player_stats_result.get("avg points") == None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Stats not found for this player and season")
    
    return player_stats_result
    

@router.get("/show-team-stats_against_team/{team_name}/{against_team}/{season}", status_code = status.HTTP_200_OK)
async def team_stats(db : db_dependency, team_name : str = Path(description = "Pass full team name"), against_team : str = Path(description = "Pass full team name"), season : str = Path(description = "Specify the season for which you want statistics.", json_schema_extra={"example": "2025-26"})):
    stmt_team_id = await db.execute(select(Teams.team_id).where(Teams.team_name == team_name).limit(1))
    result_team_id = stmt_team_id.scalar()
    if result_team_id is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Team is not exist")

    stmt_team_abbreviation = await db.execute(select(Teams.abbreviation).where(Teams.team_name == against_team).limit(1))
    result_team_abbreviation = stmt_team_abbreviation.scalar()
    if result_team_abbreviation is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Against team is not exist")

    if season not in get_season_years_list(2000):
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Season is not exist or will start soon")

    stmt_team_stats = await db.execute(select(func.round(func.avg(TeamsGameLogs.points), 1).label("avg points"),
                                                func.round(func.avg(TeamsGameLogs.assists), 1).label("avg assists"),
                                                func.round(func.avg(TeamsGameLogs.blocks), 1).label("avg blocks"),
                                                func.round(func.avg(TeamsGameLogs.steals), 1).label("avg steals"),
                                                func.round(func.avg(TeamsGameLogs.turnovers), 1).label("avg turnovers"),
                                                func.round(func.avg(TeamsGameLogs.rebounds), 1).label("avg rebounds"),
                                                func.round(func.avg(TeamsGameLogs.offensive_rebounds), 1).label("avg offensive rebounds"),
                                                func.round(func.avg(TeamsGameLogs.defensive_rebounds), 1).label("avg defensive rebounds"),
                                                func.round(func.avg(TeamsGameLogs.personal_fouls), 1).label("avg personal fouls"),
                                                func.round(func.avg(TeamsGameLogs.personal_fouls_drawn), 1).label("avg personal fouls drawn"),
                                                func.round(func.avg(TeamsGameLogs.field_goals_made), 2).label("avg field goals made"),
                                                func.round(func.avg(TeamsGameLogs.field_goals_attempted), 2).label("avg field goals attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.field_goal_percentage), Numeric), 2).label("avg field goal percentage"),
                                                func.round(func.avg(TeamsGameLogs.three_point_field_goals_made), 2).label("avg three point field goals made"),
                                                func.round(func.avg(TeamsGameLogs.three_point_field_goals_attempted), 2).label("avg three point field goals attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.three_point_field_goal_percentage), Numeric), 2).label("avg_three_point_field_goal_percentage"),
                                                func.round(func.avg(TeamsGameLogs.free_throws_made), 2).label("avg free throws made"),
                                                func.round(func.avg(TeamsGameLogs.free_throws_attempted), 2).label("avg free throws attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.free_throw_percentage), Numeric), 2).label("avg free throw percentage")   
                                              ).where(TeamsGameLogs.team_id == result_team_id, TeamsGameLogs.season == season, TeamsGameLogs.matchup.endswith(result_team_abbreviation)))
    team_stats_result = stmt_team_stats.mappings().first()
    if team_stats_result.get("avg points") == None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Stats not found for this team and this rival in this season")
    
    return team_stats_result



@router.get("/show-player-stats-against-team/{display_name}/{against_team}/{season}", status_code = status.HTTP_200_OK)
async def player_stats(db : db_dependency, display_name : str = Path(description = "Pass full player name and last name"), against_team : str = Path(description = "Pass full team name"), season : str = Path(description = "Specify the season for which you want statistics.", json_schema_extra={"example": "2025-26"})):
    stmt_player_id = await db.execute(select(Players.player_id).where(Players.display_name == display_name).limit(1))
    result_player_id = stmt_player_id.scalar()
    if result_player_id is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Player is not exist")

    stmt_team_abbreviation = await db.execute(select(Teams.abbreviation).where(Teams.team_name == against_team).limit(1))
    result_team_abbreviation = stmt_team_abbreviation.scalar()
    if result_team_abbreviation is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Team is not exist")
    
    if season not in get_season_years_list(2000):
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Season is not exist or will start soon")

    stmt_player_stats_against = await db.execute(select(func.round(cast(func.avg(PlayersGameLogs.points), Numeric), 1).label("avg points"),
                                                        func.round(func.avg(PlayersGameLogs.minutes_played), 1).label("avg minutes played"),
                                                        func.round(func.avg(PlayersGameLogs.assists), 1).label("avg assists"),
                                                        func.round(func.avg(PlayersGameLogs.blocks), 1).label("avg blocks"),
                                                        func.round(func.avg(PlayersGameLogs.steals), 1).label("avg steals"),
                                                        func.round(func.avg(PlayersGameLogs.turnovers), 1).label("avg turnovers"),
                                                        func.round(func.avg(PlayersGameLogs.rebounds), 1).label("avg rebounds"),
                                                        func.round(func.avg(PlayersGameLogs.offensive_rebounds), 1).label("avg offensive rebounds"),
                                                        func.round(func.avg(PlayersGameLogs.defensive_rebounds), 1).label("avg defensive rebounds"),
                                                        func.round(func.avg(PlayersGameLogs.personal_fouls), 1).label("avg personal fouls"),
                                                        func.round(func.avg(PlayersGameLogs.personal_fouls_drawn), 1).label("avg personal fouls drawn"),
                                                        func.round(func.avg(PlayersGameLogs.field_goals_made), 2).label("avg field goals made"),
                                                        func.round(func.avg(PlayersGameLogs.field_goals_attempted), 2).label("avg field goals attempted"),
                                                        func.round(cast(func.avg(PlayersGameLogs.field_goal_percentage), Numeric), 2).label("avg field goal percentage"),
                                                        func.round(func.avg(PlayersGameLogs.three_point_field_goals_made), 2).label("avg three point field goals made"),
                                                        func.round(func.avg(PlayersGameLogs.three_point_field_goals_attempted), 2).label("avg three point field goals attempted"),
                                                        func.round(cast(func.avg(PlayersGameLogs.three_point_field_goal_percentage), Numeric), 2).label("avg_three_point_field_goal_percentage"),
                                                        func.round(func.avg(PlayersGameLogs.free_throws_made), 2).label("avg free throws made"),
                                                        func.round(func.avg(PlayersGameLogs.free_throws_attempted), 2).label("avg free throws attempted"),
                                                        func.round(cast(func.avg(PlayersGameLogs.free_throw_percentage), Numeric), 2).label("avg free throw percentage")    
                                              ).where(PlayersGameLogs.player_id == result_player_id, PlayersGameLogs.season == season, PlayersGameLogs.matchup.endswith(result_team_abbreviation)))
    player_stats_result_against = stmt_player_stats_against.mappings().first()
    if player_stats_result_against.get("avg points") == None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Stats not found for this player and this rival in this season")
    
    return player_stats_result_against