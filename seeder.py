from nba_api.stats.static.players import get_players, get_active_players
from nba_api.stats.static.teams import get_teams
from nba_api.stats.endpoints import teamgamelogs, playergamelogs
from database import LocalSession
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Annotated
from models import Players, StatusTLog, TeamsGameLogs, PlayersGameLogs, Teams
from sqlalchemy import insert, select
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


