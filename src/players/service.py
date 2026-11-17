from fastapi import HTTPException
from sqlalchemy import select, delete, func, Numeric, cast
from database.models import *
from starlette import status
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from core.seeder import get_actual_season, get_season_years_list

async def check_user_role(user):
    if user.get("role") != "user":
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "You have no access to this page")

async def check_player_display_name(display_name, db : AsyncSession):
    stmt_player_id = await db.execute(select(Players.player_id).where(Players.display_name == display_name).limit(1))
    result_player_id = stmt_player_id.scalar()
    if result_player_id is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Player is not exists")
    return result_player_id

async def check_user_favorite_player(player_id, user, db : AsyncSession):
    stmt_check_user_favorite_players = await db.execute(select(UserFavoritePlayer).where(UserFavoritePlayer.player_id == player_id, UserFavoritePlayer.user_id == user.get("private_id")).limit(1))
    check = stmt_check_user_favorite_players.scalar()
    if check is not None:
        raise HTTPException(status_code = status.HTTP_406_NOT_ACCEPTABLE, detail = "This player is already added into your favorite players")

async def check_team_name(team_name, db : AsyncSession):
    stmt_team_id = await db.execute(select(Teams.team_id).where(Teams.team_name == team_name).limit(1))
    team_id_result = stmt_team_id.scalar()
    if team_id_result is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Team is not exists")
    return team_id_result

async def check_user_favorite_team(team_id, user, db : AsyncSession):
    stmt_check_user_favorite_teams = await db.execute(select(UserFavoriteTeam).where(UserFavoriteTeam.team_id == team_id, UserFavoriteTeam.user_id == user.get("private_id")).limit(1))
    check = stmt_check_user_favorite_teams.scalar()
    if check is not None:
        raise HTTPException(status_code = status.HTTP_406_NOT_ACCEPTABLE, detail = "This team is already added into your favorite teams")

async def check_team_abbreviation(against_team, db : AsyncSession):
    stmt_team_abbreviation = await db.execute(select(Teams.abbreviation).where(Teams.team_name == against_team).limit(1))
    result_team_abbreviation = stmt_team_abbreviation.scalar()
    if result_team_abbreviation is None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Team is not exists")
    return result_team_abbreviation

async def add_user_favorite_player(display_name, db : AsyncSession, user):
    await check_user_role(user)
    result_player_id = await check_player_display_name(display_name, db)
    await check_user_favorite_player(result_player_id, user, db)
    try:
        new_favorite_player = UserFavoritePlayer(user_id = user.get("private_id"), player_id = result_player_id)
        db.add(new_favorite_player)
        await db.commit()
        return {"message" : "Successfully added new favorite player"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error: {e}")

async def delete_user_favorite_player(display_name, db : AsyncSession, user):
    await check_user_role(user)
    result_player_id = await check_player_display_name(display_name, db)
    try:
        await db.execute(delete(UserFavoritePlayer).where(UserFavoritePlayer.user_id == user.get("private_id"), UserFavoritePlayer.player_id == result_player_id))
        await db.commit()
        return {"message" : "Successfully deleted favorite player"}
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error {e}")

async def all_user_favorite_players(db, user):
    await check_user_role(user)
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
            .where(UserFavoritePlayer.user_id == user.get("private_id"), PlayersGameLogs.season == get_actual_season())
            .group_by(UserFavoritePlayer.id, Players.display_name, Teams.team_name))
        result = stmt_user_favorite_players.mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error : {e}")

async def add_user_favorite_team(team_name, db, user):
    await check_user_role(user)
    result_team_id = await check_team_name(team_name, db)
    await check_user_favorite_team(result_team_id, user, db)
    try:
        new_favorite_team = UserFavoriteTeam(user_id = user.get("private_id"), team_id = result_team_id)
        db.add(new_favorite_team)
        await db.commit()
        return {"message" : "Successfully added new favorite team"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error: {e}")

async def delete_user_favorite_team(team_name, db, user):
    await check_user_role(user)
    result_team_id = await check_team_name(team_name, db)
    try:
        await db.execute(delete(UserFavoriteTeam).where(UserFavoriteTeam.user_id == user.get("private_id"), UserFavoriteTeam.team_id == result_team_id))
        await db.commit()
        return {"message" : "Successfully delete favorite team"}
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error {e}")

async def all_user_favorite_team(db, user):
    await check_user_role(user)
    try:
        stmt_favorite_teams = await db.execute(
            select(UserFavoriteTeam.id,
                   Teams.team_name,
                   func.round(func.avg(TeamsGameLogs.points), 1).label("avg_points"),
                   func.round(func.avg(TeamsGameLogs.assists), 1).label("avg_assists"),
                   func.round(func.avg(TeamsGameLogs.steals), 1).label("avg_steals"))
            .join(Teams, UserFavoriteTeam.team_id == Teams.team_id)
            .join(TeamsGameLogs, UserFavoriteTeam.team_id == TeamsGameLogs.team_id)
            .where(UserFavoriteTeam.user_id == user.get("private_id"), TeamsGameLogs.season == get_actual_season())
            .group_by(UserFavoriteTeam.id, Teams.team_name))
        
        result = stmt_favorite_teams.mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Unexpected error: {e}")

async def all_team_stats(team_name, season, db : AsyncSession):
    result_team_id = await check_team_name(team_name, db)

    if season not in get_season_years_list(2000):
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Season is not exist or will start soon")

    stmt_team_stats = await db.execute(select(func.round(func.avg(TeamsGameLogs.points), 1).label("avg_points"),
                                                func.round(func.avg(TeamsGameLogs.assists), 1).label("avg_assists"),
                                                func.round(func.avg(TeamsGameLogs.blocks), 1).label("avg_blocks"),
                                                func.round(func.avg(TeamsGameLogs.steals), 1).label("avg_steals"),
                                                func.round(func.avg(TeamsGameLogs.turnovers), 1).label("avg_turnovers"),
                                                func.round(func.avg(TeamsGameLogs.rebounds), 1).label("avg_rebounds"),
                                                func.round(func.avg(TeamsGameLogs.offensive_rebounds), 1).label("avg_offensive_rebounds"),
                                                func.round(func.avg(TeamsGameLogs.defensive_rebounds), 1).label("avg_defensive_rebounds"),
                                                func.round(func.avg(TeamsGameLogs.personal_fouls), 1).label("avg_personal_fouls"),
                                                func.round(func.avg(TeamsGameLogs.personal_fouls_drawn), 1).label("avg_personal_fouls_drawn"),
                                                func.round(func.avg(TeamsGameLogs.field_goals_made), 2).label("avg_field_goals_made"),
                                                func.round(func.avg(TeamsGameLogs.field_goals_attempted), 2).label("avg_field_goals_attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.field_goal_percentage), Numeric), 2).label("avg_field_goal_percentage"),
                                                func.round(func.avg(TeamsGameLogs.three_point_field_goals_made), 2).label("avg_three_point_field_goals_made"),
                                                func.round(func.avg(TeamsGameLogs.three_point_field_goals_attempted), 2).label("avg_three_point_field_goals_attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.three_point_field_goal_percentage), Numeric), 2).label("avg_three_point_field_goal_percentage"),
                                                func.round(func.avg(TeamsGameLogs.free_throws_made), 2).label("avg_free_throws_made"),
                                                func.round(func.avg(TeamsGameLogs.free_throws_attempted), 2).label("avg_free_throws_attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.free_throw_percentage), Numeric), 2).label("avg_free_throw_percentage")   
                                              ).where(TeamsGameLogs.team_id == result_team_id, TeamsGameLogs.season == season))
    team_stats_result = stmt_team_stats.mappings().first()
    if team_stats_result is None or team_stats_result.get("avg_points") == None:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Stats not found for this team and season")

    return team_stats_result

async def all_player_stats(display_name, season, db : AsyncSession):
    result_player_id = await check_player_display_name(display_name, db)
    
    if season not in get_season_years_list(2000):
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Season is not exist or will start soon")

    stmt_player_stats = await db.execute(select(func.round(cast(func.avg(PlayersGameLogs.points), Numeric), 1).label("avg_points"),
                                                func.round(func.avg(PlayersGameLogs.assists), 1).label("avg_assists"),
                                                func.round(func.avg(PlayersGameLogs.blocks), 1).label("avg_blocks"),
                                                func.round(func.avg(PlayersGameLogs.steals), 1).label("avg_steals"),
                                                func.round(func.avg(PlayersGameLogs.turnovers), 1).label("avg_turnovers"),
                                                func.round(func.avg(PlayersGameLogs.rebounds), 1).label("avg_rebounds"),
                                                func.round(func.avg(PlayersGameLogs.offensive_rebounds), 1).label("avg_offensive_rebounds"),
                                                func.round(func.avg(PlayersGameLogs.defensive_rebounds), 1).label("avg_defensive_rebounds"),
                                                func.round(func.avg(PlayersGameLogs.personal_fouls), 1).label("avg_personal_fouls"),
                                                func.round(func.avg(PlayersGameLogs.personal_fouls_drawn), 1).label("avg_personal_fouls_drawn"),
                                                func.round(func.avg(PlayersGameLogs.field_goals_made), 2).label("avg_field_goals_made"),
                                                func.round(func.avg(PlayersGameLogs.field_goals_attempted), 2).label("avg_field_goals_attempted"),
                                                func.round(cast(func.avg(PlayersGameLogs.field_goal_percentage), Numeric), 2).label("avg_field_goal_percentage"),
                                                func.round(func.avg(PlayersGameLogs.three_point_field_goals_made), 2).label("avg_three_point_field_goals_made"),
                                                func.round(func.avg(PlayersGameLogs.three_point_field_goals_attempted), 2).label("avg_three_point_field_goals_attempted"),
                                                func.round(cast(func.avg(PlayersGameLogs.three_point_field_goal_percentage), Numeric), 2).label("avg_three_point_field_goal_percentage"),
                                                func.round(func.avg(PlayersGameLogs.free_throws_made), 2).label("avg_free_throws_made"),
                                                func.round(func.avg(PlayersGameLogs.free_throws_attempted), 2).label("avg_free_throws_attempted"),
                                                func.round(cast(func.avg(PlayersGameLogs.free_throw_percentage), Numeric), 2).label("avg_free_throw_percentage")    
                                              ).where(PlayersGameLogs.player_id == result_player_id, PlayersGameLogs.season == season))
    player_stats_result = stmt_player_stats.mappings().first()
    if player_stats_result is None or player_stats_result.get("avg_points") == None:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Stats not found for this player and season")
    return player_stats_result

async def compare_team_to_team(team_name, against_team, season, db : AsyncSession):
    result_team_id = await check_team_name(team_name, db)
    result_team_abbreviation = await check_team_abbreviation(against_team, db)

    if season not in get_season_years_list(2000):
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Season is not exist or will start soon")

    stmt_team_stats = await db.execute(select(func.round(func.avg(TeamsGameLogs.points), 1).label("avg_points"),
                                                func.round(func.avg(TeamsGameLogs.assists), 1).label("avg_assists"),
                                                func.round(func.avg(TeamsGameLogs.blocks), 1).label("avg_blocks"),
                                                func.round(func.avg(TeamsGameLogs.steals), 1).label("avg_steals"),
                                                func.round(func.avg(TeamsGameLogs.turnovers), 1).label("avg_turnovers"),
                                                func.round(func.avg(TeamsGameLogs.rebounds), 1).label("avg_rebounds"),
                                                func.round(func.avg(TeamsGameLogs.offensive_rebounds), 1).label("avg_offensive_rebounds"),
                                                func.round(func.avg(TeamsGameLogs.defensive_rebounds), 1).label("avg_defensive_rebounds"),
                                                func.round(func.avg(TeamsGameLogs.personal_fouls), 1).label("avg_personal_fouls"),
                                                func.round(func.avg(TeamsGameLogs.personal_fouls_drawn), 1).label("avg_personal_fouls_drawn"),
                                                func.round(func.avg(TeamsGameLogs.field_goals_made), 2).label("avg_field_goals_made"),
                                                func.round(func.avg(TeamsGameLogs.field_goals_attempted), 2).label("avg_field_goals_attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.field_goal_percentage), Numeric), 2).label("avg_field_goal_percentage"),
                                                func.round(func.avg(TeamsGameLogs.three_point_field_goals_made), 2).label("avg_three_point_field_goals_made"),
                                                func.round(func.avg(TeamsGameLogs.three_point_field_goals_attempted), 2).label("avg_three_point_field_goals_attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.three_point_field_goal_percentage), Numeric), 2).label("avg_three_point_field_goal_percentage"),
                                                func.round(func.avg(TeamsGameLogs.free_throws_made), 2).label("avg_free_throws_made"),
                                                func.round(func.avg(TeamsGameLogs.free_throws_attempted), 2).label("avg_free_throws_attempted"),
                                                func.round(cast(func.avg(TeamsGameLogs.free_throw_percentage), Numeric), 2).label("avg_free_throw_percentage")   
                                              ).where(TeamsGameLogs.team_id == result_team_id, TeamsGameLogs.season == season, TeamsGameLogs.matchup.endswith(result_team_abbreviation)))
    team_stats_result = stmt_team_stats.mappings().first()
    if team_stats_result is None or team_stats_result.get("avg_points") == None:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Stats not found for this team and this rival in this season")
    return team_stats_result

async def compare_player_to_team(display_name, against_team, season, db):
    result_player_id = await check_player_display_name(display_name, db)
    result_team_abbreviation = await check_team_abbreviation(against_team, db)
    
    if season not in get_season_years_list(2000):
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Season is not exist or will start soon")

    stmt_player_stats_against = await db.execute(select(func.round(cast(func.avg(PlayersGameLogs.points), Numeric), 1).label("avg_points"),
                                                        func.round(func.avg(PlayersGameLogs.minutes_played), 1).label("avg_minutes_played"),
                                                        func.round(func.avg(PlayersGameLogs.assists), 1).label("avg_assists"),
                                                        func.round(func.avg(PlayersGameLogs.blocks), 1).label("avg_blocks"),
                                                        func.round(func.avg(PlayersGameLogs.steals), 1).label("avg_steals"),
                                                        func.round(func.avg(PlayersGameLogs.turnovers), 1).label("avg_turnovers"),
                                                        func.round(func.avg(PlayersGameLogs.rebounds), 1).label("avg_rebounds"),
                                                        func.round(func.avg(PlayersGameLogs.offensive_rebounds), 1).label("avg_offensive_rebounds"),
                                                        func.round(func.avg(PlayersGameLogs.defensive_rebounds), 1).label("avg_defensive_rebounds"),
                                                        func.round(func.avg(PlayersGameLogs.personal_fouls), 1).label("avg_personal_fouls"),
                                                        func.round(func.avg(PlayersGameLogs.personal_fouls_drawn), 1).label("avg_personal_fouls_drawn"),
                                                        func.round(func.avg(PlayersGameLogs.field_goals_made), 2).label("avg_field_goals_made"),
                                                        func.round(func.avg(PlayersGameLogs.field_goals_attempted), 2).label("avg_field_goals_attempted"),
                                                        func.round(cast(func.avg(PlayersGameLogs.field_goal_percentage), Numeric), 2).label("avg_field_goal_percentage"),
                                                        func.round(func.avg(PlayersGameLogs.three_point_field_goals_made), 2).label("avg_three_point_field_goals_made"),
                                                        func.round(func.avg(PlayersGameLogs.three_point_field_goals_attempted), 2).label("avg_three_point_field_goals_attempted"),
                                                        func.round(cast(func.avg(PlayersGameLogs.three_point_field_goal_percentage), Numeric), 2).label("avg_three_point_field_goal_percentage"),
                                                        func.round(func.avg(PlayersGameLogs.free_throws_made), 2).label("avg_free_throws_made"),
                                                        func.round(func.avg(PlayersGameLogs.free_throws_attempted), 2).label("avg_free_throws_attempted"),
                                                        func.round(cast(func.avg(PlayersGameLogs.free_throw_percentage), Numeric), 2).label("avg_free_throw_percentage")    
                                              ).where(PlayersGameLogs.player_id == result_player_id, PlayersGameLogs.season == season, PlayersGameLogs.matchup.endswith(result_team_abbreviation)))
    player_stats_result_against = stmt_player_stats_against.mappings().first()
    if player_stats_result_against is None or player_stats_result_against.get("avg_points") == None:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Stats not found for this player and this rival in this season")
    
    return player_stats_result_against