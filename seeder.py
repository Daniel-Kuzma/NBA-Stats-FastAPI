from nba_api.stats.static.players import get_players, get_active_players
from nba_api.stats.static.teams import get_teams
from nba_api.stats.endpoints import teamgamelogs, playergamelogs, commonallplayers
from database import LocalSession
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Annotated
from models import Players, StatusTLog, TeamsGameLogs, PlayersGameLogs, Teams
from sqlalchemy import insert, select, update
from asyncio import sleep
from starlette import status
from datetime import datetime


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


# funkcja która szuka graczy którzy grali w sezonie regularnym ale z jakiegoś powodu nie są dodawania przez biblioteke nba_api
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

    
