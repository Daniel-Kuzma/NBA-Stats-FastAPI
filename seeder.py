from nba_api.stats.static.players import get_players, get_active_players
from nba_api.stats.static.teams import get_teams
from nba_api.stats.endpoints import teamgamelogs, playergamelogs, commonallplayers
from database import LocalSession
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Annotated
from models import Players, StatusTLog, TeamsGameLogs, PlayersGameLogs, Teams
from sqlalchemy import insert, select, update, desc
from asyncio import sleep
from starlette import status
from datetime import datetime
import pandas as pd

async def get_db():
    async with LocalSession as db:
        yield db


db_dependency = Annotated[AsyncSession, Depends(get_db)]

def get_season_years_list(start_season):
    actual_year = datetime.now().year
    season_id_list = []

    for years in range(start_season, actual_year+1):
        second_part_of_season_id = years + 1
        season_id = str(years) + "-" + str(second_part_of_season_id)[2:]
        season_id_list.append(season_id)
    return season_id_list


# funkcja która szuka graczy którzy grali w sezonie regularnym ale nie są dodawania przez biblioteke nba_api
def missing_players_tracker(db: db_dependency):
    players = get_players()
    known_player_ids = {p["id"] for p in players}
    missing_players = []
    already_found_ids = set() 

    season_id_list = get_season_years_list(2025)

    for season_id in season_id_list:
        all_py = playergamelogs.PlayerGameLogs(season_nullable=season_id, season_type_nullable="Regular Season")
        df = all_py.get_data_frames()[0]
        unknown_logs = df[~df["PLAYER_ID"].isin(known_player_ids)]
        unique_unknown_players = unknown_logs.drop_duplicates(subset=["PLAYER_ID"])
        
        for index, row in unique_unknown_players.iterrows():
            player_id = row["PLAYER_ID"]
            full_name = row["PLAYER_NAME"]
            if player_id not in already_found_ids:
                already_found_ids.add(player_id)
                name_parts = full_name.split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                missing_players.append({
                    "player_id": player_id,
                    "player_name": first_name,
                    "player_last_name": last_name,
                    "is_active": True 
                })
    return missing_players


# {'PERSON_ID': 203507, 'DISPLAY_LAST_COMMA_FIRST': 'Antetokounmpo, Giannis',
#  'DISPLAY_FIRST_LAST': 'Giannis Antetokounmpo', 'ROSTERSTATUS': 1,
#  'FROM_YEAR': '2013', 'TO_YEAR': '2026', 'PLAYERCODE': 'giannis_antetokounmpo',
#  'PLAYER_SLUG': 'giannis_antetokounmpo', 'TEAM_ID': 1610612748, 'TEAM_CITY': 'Miami',
#  'TEAM_NAME': 'Heat', 'TEAM_ABBREVIATION': 'MIA', 'TEAM_SLUG': 'heat',
#  'TEAM_CODE': 'heat', 'GAMES_PLAYED_FLAG': 'Y', 'OTHERLEAGUE_EXPERIENCE_CH': '00'}

def get_actual_season():
    actual_month = datetime.now().month
    if actual_month >= 10:
        year = datetime.now().year
        slice_year = year + 1
        year_string = str(year)
        slice_year_string = str(slice_year)
        season = year_string + "-" + slice_year_string[2:]
        return season
    else:
        year = datetime.now().year - 1
        slice_year = year + 1
        year_string = str(year)
        slice_year_string = str(slice_year)
        season = year_string + "-" + slice_year_string[2:]
        return season



# funkcja ma na celu znaleźć aktywnych graczy z aktualnego sezonu
async def check_active_players(db:db_dependency):
    season = get_season_years_list(datetime.now().year-1)
    live_players_data = commonallplayers.CommonAllPlayers(is_only_current_season=1, season=season[-1])
    players_data = live_players_data.get_normalized_dict()
    if players_data["CommonAllPlayers"]:
        actual_season = season[-1]
    else:
        actual_season = season[0]

    live_players_data = commonallplayers.CommonAllPlayers(is_only_current_season=1, season=actual_season)
    player_df = live_players_data.get_data_frames()[0]
    stmt = select(Players.player_id)
    result = await db.execute(stmt)
    respond = result.scalars()
    for x in respond:
        if (player_df["PERSON_ID"] == x).any():
            player_team = player_df[player_df["PERSON_ID"] == x]
            team_id = player_team["TEAM_ID"].values
            try:
                await db.execute(update(Players).where(Players.player_id == x).values(is_active = 1, player_team = int(team_id[0])))
                await db.commit()
            except Exception as e:
                await db.rollback()
                print(f"something goes wrong : {e}")
                break


async def set_all_players_teams(db:db_dependency):

    stm_players_id = select(Players.player_id)
    result_players_id = await db.execute(stm_players_id)
    respond_player_id = result_players_id.scalars()

    stm_last_player_team = select(PlayersGameLogs.player_id, PlayersGameLogs.team_id).distinct(PlayersGameLogs.player_id).order_by(PlayersGameLogs.player_id, PlayersGameLogs.game_date.desc())
    result_last_player_team = await db.execute(stm_last_player_team)
    respond_last_player_team = result_last_player_team.all()

    for id in respond_player_id:
        for player_team in respond_last_player_team:
            if id == player_team[0]:
                try:
                    await db.execute(update(Players).where(Players.player_id == id).values(player_team = player_team[1]))
                    await db.commit()
                except Exception as e:
                    db.rollback()
                    print(f"something goes wrong: {e}")

async def upload_new_player_logs(db:db_dependency):
    chunk_size = 1000
    downloaded_data = 0
    log_status = True

    game_logs_upload = playergamelogs.PlayerGameLogs(season_nullable=get_actual_season(), season_type_nullable="Regular Season")
    game_logs = game_logs_upload.get_normalized_dict()["PlayerGameLogs"]
    game_logs_tuple = set()
    for x in game_logs:
        game_logs_tuple.add((x["PLAYER_ID"], x["GAME_ID"]))

    stmt_players_log = select(PlayersGameLogs).where(PlayersGameLogs.season == get_actual_season())
    result_player_log = await db.execute(stmt_players_log)
    respond_plyer_log = result_player_log.scalars()
    respond_plyer_log_tuple = set()
    for x in respond_plyer_log:
        respond_plyer_log_tuple.add((x.player_id, x.game_id))

    missing_player_logs = []
    for x in game_logs_tuple:
        if x not in respond_plyer_log_tuple:
            missing_player_logs.append(x)    

    players_logs_dict = []

    try:
        for log in missing_player_logs:
            for logs in game_logs:
                if log[0] == logs["PLAYER_ID"] and log[1] == logs["GAME_ID"]:
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
        await db.rollback()
        print(f"Somethings goes wrong: {e}")
        log_status = False

    try:
        new_log = StatusTLog(log_description = "Upload new players logs",
                            downloaded_records = downloaded_data,
                            completed = log_status,
                            log_type = "players_log")
        db.add(new_log)
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error trying add log: {e}")


async def upload_new_teams_logs(db:db_dependency):
    chunk_size = 1000
    downloaded_data = 0
    log_status = True

    game_logs_upload = teamgamelogs.TeamGameLogs(season_nullable=get_actual_season(), season_type_nullable="Regular Season")
    game_logs = game_logs_upload.get_normalized_dict()["TeamGameLogs"]
    game_logs_tuple = set()
    for x in game_logs:
        game_logs_tuple.add((x["GAME_ID"], x["TEAM_ID"]))

    stmt_teams_log = select(TeamsGameLogs).where(TeamsGameLogs.season == get_actual_season())
    result_teams_log = await db.execute(stmt_teams_log)
    respond_teams_log = result_teams_log.scalars()
    respond_teams_log_tuple = set()
    for x in respond_teams_log:
        respond_teams_log_tuple.add((x.game_id, x.team_id))

    missing_teams_logs = []
    for x in game_logs_tuple:
        if x not in respond_teams_log_tuple:
            missing_teams_logs.append(x)    
    api_logs_dict_lookup = {(x["GAME_ID"], x["TEAM_ID"]): x for x in game_logs}
    teams_logs_dict = []
    try:
        for log_tuple in missing_teams_logs:
            logs = api_logs_dict_lookup[log_tuple]  
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
        await db.rollback()
        print(f"Somethings goes wrong: {e}")
        log_status = False

    try:
        new_log = StatusTLog(log_description = "Upload new teams logs",
                            downloaded_records = downloaded_data,
                            completed = log_status,
                            log_type = "teams_log")
        db.add(new_log)
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error trying add log: {e}")