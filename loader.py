from nba_api.stats.static.players import get_players
from nba_api.stats.static.teams import get_teams
from nba_api.stats.endpoints import teamgamelogs, playergamelogs, commonallplayers
from database import LocalSession
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Annotated
from models import Players, StatusTLog, TeamsGameLogs, PlayersGameLogs, Teams
from sqlalchemy import insert, select
from datetime import datetime
from asyncio import sleep
from starlette import status
from seeder import missing_players_tracker, get_season_years_list


async def get_db():
    async with LocalSession() as db:
        yield db

db_dependency = Annotated[AsyncSession, Depends(get_db)]

async def add_players_to_database(db:db_dependency):
    players = get_players()
    log_status = True
    players_dict = []
    chunk_size = 1000

    stmt = select(Players).limit(1)
    result = await db.execute(stmt)
    database_respond = result.scalar()

    if database_respond is None:
        try: 
            for player in players:
                players_dict.append({"player_id" : player["id"],
                                    "player_name" : player["first_name"],
                                    "player_last_name" : player["last_name"],
                                    "is_active" : player["is_active"]})

            players_dict += missing_players_tracker(db=db)
            for i in range(0, len(players_dict), chunk_size):
                chunk = players_dict[i:i + chunk_size]
                await db.execute(insert(Players), chunk)
            await db.commit()


        except Exception as e:
            await db.rollback()
            log_status = False
            print(f"Error trying to add players: {e}")
        finally:
            if log_status:
                print("Successfully added players")

    try:
        new_log = StatusTLog(log_description = "Add active players",
                            downloaded_records = len(players_dict),
                            completed = log_status,
                            log_type = "players_list")
        db.add(new_log)
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error trying to add log: {e}")

async def add_teams_to_database(db:db_dependency):
    teams = get_teams()
    log_status = True
    teams_dict = []
    chunk_size = 1000

    stmt = select(Teams).limit(1)
    result = await db.execute(stmt)
    database_respond = result.scalar()

    if database_respond is None:
        try:
            for team in teams:
                teams_dict.append({"team_id" : team["id"],
                                "team_name" : team["full_name"],
                                "abbreviation" : team["abbreviation"]})
            for i in range(0, len(teams_dict), chunk_size):
                chunk = teams_dict[i:i + chunk_size]
                await db.execute(insert(Teams), chunk)
            await db.commit()

        except Exception as e:
            log_status = False
            await db.rollback()
            print(f"Error trying to add teams: {e}")
        finally:
            if log_status:
                print("Successfully added teams")

    try:
        new_log = StatusTLog(log_description = "Add teams",
                                    downloaded_records = len(teams_dict),
                                    completed = log_status,
                                    log_type = "teams_list")
        db.add(new_log)
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error trying to add log: {e}")

async def add_teams_game_logs(db:db_dependency):
    log_status = True
    season_id_list = get_season_years_list(2000)
    chunk_size = 1000
    downloaded_data = 0

    try:
        for season_id in season_id_list:

            stmt = select(TeamsGameLogs).where(TeamsGameLogs.season == season_id).limit(1)
            result =  await db.execute(stmt)
            season = result.scalar()

            if season is None:
                team_game_logs = teamgamelogs.TeamGameLogs(season_nullable = season_id, season_type_nullable = "Regular Season")
                team_game_logs_dict = team_game_logs.get_normalized_dict()
                teams_logs = team_game_logs_dict["TeamGameLogs"]

                teams_logs_dict = []

                for logs in teams_logs:
                    win_or_lose = (logs["WL"] == "W")
                    fg_pct = logs["FG_PCT"] * 100
                    fg3_pct = logs["FG3_PCT"] * 100
                    ft_pct = logs["FT_PCT"] * 100
                    date_time = datetime.fromisoformat(logs["GAME_DATE"])

                    teams_logs_dict.append({"season" : logs["SEASON_YEAR"],
                                            "team_id" : logs["TEAM_ID"],
                                            "game_id" : logs["GAME_ID"],
                                            "game_date" : date_time,
                                            "matchup" : logs["MATCHUP"],
                                            "is_win" : win_or_lose,
                                            "field_goals_made" : logs["FGM"],
                                            "field_goals_attempted" : logs["FGA"],
                                            "field_goal_percentage" : fg_pct,
                                            "three_point_field_goals_made" : logs["FG3M"],
                                            "three_point_field_goals_attempted" : logs["FG3A"],
                                            "three_point_field_goal_percentage" : fg3_pct,
                                            "free_throws_made" : logs["FTM"],
                                            "free_throws_attempted" : logs["FTA"],
                                            "free_throw_percentage" : ft_pct,
                                            "offensive_rebounds" : logs["OREB"],
                                            "defensive_rebounds" : logs["DREB"],
                                            "rebounds" : logs["REB"],
                                            "assists" : logs["AST"],
                                            "turnovers" : logs["TOV"],
                                            "steals" : logs["STL"],
                                            "blocks" : logs["BLK"],
                                            "blocks_against" : logs["BLKA"],
                                            "personal_fouls" : logs["PF"],
                                            "personal_fouls_drawn" : logs["PFD"],
                                            "points" : logs["PTS"]})
                if teams_logs_dict:
                    for i in range(0, len(teams_logs_dict), chunk_size):
                        chunk = teams_logs_dict[i:i + chunk_size]
                        await db.execute(insert(TeamsGameLogs), chunk)
                    await db.commit()

                    downloaded_data += len(teams_logs_dict)
            await sleep(2)
        
    except Exception as e:
        log_status = False
        await db.rollback()
        print(f"Error trying add teams logs: {e}")
    finally:
        if log_status:
            print("Successfully added teams logs")

    try:
        new_log = StatusTLog(log_description = "Add teams logs",
                            downloaded_records = downloaded_data,
                            completed = log_status,
                            log_type = "teams_log")
        db.add(new_log)
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error trying add log: {e}")

async def add_players_game_logs(db:db_dependency):
    log_status = True
    season_id_list = get_season_years_list(2000)
    downloaded_data = 0
    chunk_size = 1000

    try:
        for season_id in season_id_list:
            stmt = select(PlayersGameLogs).where(PlayersGameLogs.season == season_id).limit(1)
            result = await db.execute(stmt)
            season = result.scalar()
            if season is None:

                player_game_logs = playergamelogs.PlayerGameLogs(season_nullable = "2025-26", season_type_nullable = "Regular Season")
                player_game_logs_dict = player_game_logs.get_normalized_dict()
                players_logs = player_game_logs_dict["PlayerGameLogs"]

                players_logs_dict = []

                for logs in players_logs:
                    win_or_lose = (logs["WL"] == "W")
                    fg_pct = logs["FG_PCT"] * 100
                    fg3_pct = logs["FG3_PCT"] * 100
                    ft_pct = logs["FT_PCT"] * 100
                    date_time = datetime.fromisoformat(logs["GAME_DATE"])
                    players_logs_dict.append({"season" : logs["SEASON_YEAR"],
                                            "player_id" : logs["PLAYER_ID"],
                                            "team_id" : logs["TEAM_ID"],
                                            "game_id" : logs["GAME_ID"],
                                            "game_date" : date_time,
                                            "matchup" : logs["MATCHUP"],
                                            "is_win" : win_or_lose,
                                            "minutes_played" : logs["MIN"],
                                            "field_goals_made" : logs["FGM"],
                                            "field_goals_attempted" : logs["FGA"],
                                            "field_goal_percentage" : fg_pct,
                                            "three_point_field_goals_made" : logs["FG3M"],
                                            "three_point_field_goals_attempted" : logs["FG3A"],
                                            "three_point_field_goal_percentage" : fg3_pct,
                                            "free_throws_made" : logs["FTM"],
                                            "free_throws_attempted" : logs["FTA"],
                                            "free_throw_percentage" : ft_pct,
                                            "offensive_rebounds" : logs["OREB"],
                                            "defensive_rebounds" : logs["DREB"],
                                            "rebounds" : logs["REB"],
                                            "assists" : logs["AST"],
                                            "turnovers" : logs["TOV"],
                                            "steals" : logs["STL"],
                                            "blocks" : logs["BLK"],
                                            "blocks_against" : logs["BLKA"],
                                            "personal_fouls" : logs["PF"],
                                            "personal_fouls_drawn" : logs["PFD"],
                                            "points" : logs["PTS"]})
                if players_logs_dict:
                    for i in range(0, len(players_logs_dict), chunk_size):
                        chunk = players_logs_dict[i:i + chunk_size]
                        await db.execute(insert(PlayersGameLogs), chunk)
                    await db.commit()
                    downloaded_data += len(players_logs_dict)
            await sleep(2)
    except Exception as e:
        log_status = False
        await db.rollback()
        print(f"Error trying add players logs: {e}")
    finally:
        if log_status:
            print("Successfully added players logs")

    try:
        new_log = StatusTLog(log_description = "Add players logs",
                            downloaded_records = downloaded_data,
                            completed = log_status,
                            log_type = "players_log")
        db.add(new_log)
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error trying add log: {e}")