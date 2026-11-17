from test.utils import *
from database.core import get_db
from auth.service import get_current_user
from fastapi import status
import pytest
from sqlalchemy import select, delete

app.dependency_overrides[get_db] = override_get_db

@pytest.mark.asyncio
async def test_add_favorite_player(test_data_players, test_data_users):
    app.dependency_overrides[get_current_user] = override_get_current_user
    respons = client.post("/user/add-favorite-player/James Lebron")
    assert respons.status_code == status.HTTP_201_CREATED
    async with TestingSessionLocal() as db:
        stmt = await db.execute(select(models.UserFavoritePlayer).where(models.UserFavoritePlayer.player_id == 2).limit(1))
        result = stmt.one_or_none()
        assert result != None

@pytest.mark.asyncio
async def test_add_favorite_player_if_player_is_favorite(test_data_users, test_data_players, test_data_favorite_player):
    respons = client.post("/user/add-favorite-player/Kevin Durant")
    assert respons.status_code == status.HTTP_406_NOT_ACCEPTABLE

@pytest.mark.asyncio
async def test_add_favorite_player_if_dose_not_exist(test_data_users, test_data_players):
    respons = client.post("/user/add-favorite-player/Kevin James")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_delete_favorite_player(test_data_users, test_data_players, test_data_favorite_player):
    respons = client.delete("/user/delete-favorite-player/Kevin Durant")
    assert respons.status_code == status.HTTP_200_OK
    async with TestingSessionLocal() as db:
        stmt = await db.execute(select(models.UserFavoritePlayer).where(models.UserFavoritePlayer.player_id == 1).limit(1))
        result = stmt.one_or_none()
        assert result == None

@pytest.mark.asyncio
async def test_delete_player_if_player_is_not_favorite(test_data_users, test_data_players):
    respons = client.delete("/user/delete-favorite-player/James Lebron")
    assert respons.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_delete_favorite_player_if_dose_not_exist(test_data_users, test_data_players):
    respons = client.delete("/user/delete-favorite-player/Kevin James")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_user_favorite_players(test_data_users, test_data_favorite_player, test_data_teams, test_data_players, test_data_player_logs):
    respons = client.get("/user/user-favorite-players")
    assert respons.status_code == status.HTTP_200_OK
    assert respons.json()[0] == {"display_name" : "Kevin Durant",
                                 "team_name" : "Huston Rockets",
                                 "avg_points" : 34.0,
                                 "avg_assist" : 3.0,
                                 "avg_steals" : 1.0}

@pytest.mark.asyncio
async def test_user_favorite_players_if_none_player_is_add(test_data_users, test_data_favorite_player, test_data_teams, test_data_players, test_data_player_logs):
    async with TestingSessionLocal() as db:
        await db.execute(delete(models.UserFavoritePlayer).where(models.UserFavoritePlayer.player_id == 1))
        respons = client.get("/user/user-favorite-players")
        assert respons.status_code == status.HTTP_200_OK
        assert respons.json() == []

@pytest.mark.asyncio
async def test_add_favorite_team(test_data_users, test_data_teams):
    respons = client.post("/user/add-favorite-team/Los Angeles Lakers")
    assert respons.status_code == status.HTTP_201_CREATED
    async with TestingSessionLocal() as db:
        stm = await db.execute(select(models.UserFavoriteTeam).where(models.UserFavoriteTeam.team_id == 2).limit(1))
        result = stm.one_or_none()
        assert result != None

@pytest.mark.asyncio
async def test_add_favorite_team_if_team_is_favorite(test_data_users, test_data_teams, test_data_favorite_team):
    respons = client.post("/user/add-favorite-team/Huston Rockets")
    assert respons.status_code == status.HTTP_406_NOT_ACCEPTABLE

@pytest.mark.asyncio
async def test_add_favorite_team_if_dose_not_exist(test_data_users, test_data_teams):
    respons = client.post("/user/add-favorite-team/Los Huston Lakers")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_delete_favorite_team(test_data_users, test_data_teams, test_data_favorite_team):
    respons = client.delete("/user/delete-favorite-team/Huston Rockets")
    assert respons.status_code == status.HTTP_200_OK
    async with TestingSessionLocal() as db:
        stmt = await db.execute(select(models.UserFavoriteTeam).where(models.UserFavoriteTeam.team_id == 1).limit(1))
        result = stmt.one_or_none()
        assert result == None

@pytest.mark.asyncio
async def test_delete_team_if_team_is_not_favorite(test_data_users, test_data_teams):
    respons = client.delete("/user/delete-favorite-team/Los Angeles Lakers")
    assert respons.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_delete_favorite_team_if_dose_not_exist(test_data_users, test_data_teams):
    respons = client.delete("/user/delete-favorite-team/Huston Lakers")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_user_favorite_teams(test_data_users, test_data_favorite_team, test_data_teams, test_data_team_logs):
    respons = client.get("/user/user-favorite-teams")
    assert respons.status_code == status.HTTP_200_OK
    assert respons.json()[0] == {"team_name" : "Huston Rockets",
                                 "avg_points" : 120.0,
                                 "avg_assists" : 20.0,
                                 "avg_steals" : 5.0}

@pytest.mark.asyncio
async def test_user_favorite_teams_if_none_team_is_add(test_data_users, test_data_favorite_team, test_data_teams, test_data_team_logs):
    async with TestingSessionLocal() as db:
        await db.execute(delete(models.UserFavoriteTeam).where(models.UserFavoriteTeam.team_id == 1))
        respons = client.get("/user/user-favorite-teams")
        assert respons.status_code == status.HTTP_200_OK
        assert respons.json() == []

@pytest.mark.asyncio
async def test_show_team_stats(test_data_team_logs, test_data_teams):
    respons = client.get("/user/show-team-stats/Huston Rockets/2025-26")
    assert respons.status_code == status.HTTP_200_OK
    assert respons.json() == {"avg_points" : 120.0,
                            "avg_assists" : 20.0,  
                            "avg_blocks" : 5.0, 
                            "avg_steals" : 5.0,
                            "avg_turnovers" : 10.0,
                            "avg_rebounds" : 25.0,
                            "avg_offensive_rebounds" : 10.0,
                            "avg_defensive_rebounds" : 15.0,
                            "avg_personal_fouls" : 12.0,
                            "avg_personal_fouls_drawn" : 14.0,
                            "avg_field_goals_made" : 40.0,
                            "avg_field_goals_attempted" : 50.0,
                            "avg_field_goal_percentage" : 80.0,
                            "avg_three_point_field_goals_made" : 5.0,
                            "avg_three_point_field_goals_attempted" : 10.0,
                            "avg_three_point_field_goal_percentage" : 50.0,
                            "avg_free_throws_made" : 10.0,
                            "avg_free_throws_attempted" : 15.0,
                            "avg_free_throw_percentage" : 67.0}

@pytest.mark.asyncio
async def test_show_team_stats_if_team_is_not_exist(test_data_team_logs, test_data_teams):
    respons = client.get("/user/show-team-stats/Huston Lakers/2025-26")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Team is not exists"}

@pytest.mark.asyncio
async def test_show_team_stats_if_season_is_not_exist(test_data_team_logs, test_data_teams):
    respons = client.get("/user/show-team-stats/Huston Rockets/2028-29")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Season is not exist or will start soon"}

@pytest.mark.asyncio
async def test_show_team_stats_if_team_is_not_play_yet(test_data_team_logs, test_data_teams):
    respons = client.get("/user/show-team-stats/Los Angeles Lakers/2025-26")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Stats not found for this team and season"}

@pytest.mark.asyncio
async def test_show_player_stats(test_data_player_logs, test_data_players):
    respons = client.get("/user/show-player-stats/Kevin Durant/2025-26")
    assert respons.status_code == status.HTTP_200_OK
    assert respons.json() == {"avg_points" : 34.0,
                            "avg_assists" : 3.0,  
                            "avg_blocks" : 3.0, 
                            "avg_steals" : 1.0,
                            "avg_turnovers" : 2.0,
                            "avg_rebounds" : 8.0,
                            "avg_offensive_rebounds" : 5.0,
                            "avg_defensive_rebounds" : 3.0,
                            "avg_personal_fouls" : 1.0,
                            "avg_personal_fouls_drawn" : 1.0,
                            "avg_field_goals_made" : 15.0,
                            "avg_field_goals_attempted" : 20.0,
                            "avg_field_goal_percentage" : 80.0,
                            "avg_three_point_field_goals_made" : 2.0,
                            "avg_three_point_field_goals_attempted" : 4.0,
                            "avg_three_point_field_goal_percentage" : 50.0,
                            "avg_free_throws_made" : 4.0,
                            "avg_free_throws_attempted" : 4.0,
                            "avg_free_throw_percentage" : 100.0}

@pytest.mark.asyncio
async def test_show_player_stats_if_player_is_not_exist(test_data_player_logs, test_data_players):
    respons = client.get("/user/show-player-stats/Kevin Lebron/2025-26")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Player is not exists"}

@pytest.mark.asyncio
async def test_show_player_stats_if_season_is_not_exist(test_data_player_logs, test_data_players):
    respons = client.get("/user/show-player-stats/Kevin Durant/2028-29")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Season is not exist or will start soon"}

@pytest.mark.asyncio
async def test_show_player_stats_if_team_is_not_play_yet(test_data_player_logs, test_data_players):
    respons = client.get("/user/show-player-stats/James Lebron/2025-26")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Stats not found for this player and season"}

@pytest.mark.asyncio
async def test_show_team_stats_against_team(test_data_team_logs, test_data_teams):
    respons = client.get("/user/show-team-stats_against_team/Huston Rockets/Los Angeles Lakers/2025-26")
    assert respons.status_code == status.HTTP_200_OK
    assert respons.json() == {"avg_points" : 120.0,
                            "avg_assists" : 20.0,  
                            "avg_blocks" : 5.0, 
                            "avg_steals" : 5.0,
                            "avg_turnovers" : 10.0,
                            "avg_rebounds" : 25.0,
                            "avg_offensive_rebounds" : 10.0,
                            "avg_defensive_rebounds" : 15.0,
                            "avg_personal_fouls" : 12.0,
                            "avg_personal_fouls_drawn" : 14.0,
                            "avg_field_goals_made" : 40.0,
                            "avg_field_goals_attempted" : 50.0,
                            "avg_field_goal_percentage" : 80.0,
                            "avg_three_point_field_goals_made" : 5.0,
                            "avg_three_point_field_goals_attempted" : 10.0,
                            "avg_three_point_field_goal_percentage" : 50.0,
                            "avg_free_throws_made" : 10.0,
                            "avg_free_throws_attempted" : 15.0,
                            "avg_free_throw_percentage" : 67.0}

@pytest.mark.asyncio
async def test_show_team_stats_against_team_if_team_is_not_exist(test_data_team_logs, test_data_teams):
    respons = client.get("/user/show-team-stats_against_team/Huston /Los Angeles Lakers/2025-26")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Team is not exists"}

@pytest.mark.asyncio
async def test_show_team_stats_against_team_if_against_team_is_not_exist(test_data_team_logs, test_data_teams):
    respons = client.get("/user/show-team-stats_against_team/Huston Rockets/Los Lakers/2025-26")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Team is not exists"}

@pytest.mark.asyncio
async def test_show_team_stats_against_team_if_season_not_exist(test_data_team_logs, test_data_teams):
    respons = client.get("/user/show-team-stats_against_team/Huston Rockets/Los Angeles Lakers/2028-29")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Season is not exist or will start soon"}

@pytest.mark.asyncio
async def test_show_team_stats_against_team_if_they_not_played(test_data_team_logs, test_data_teams):
    respons = client.get("/user/show-team-stats_against_team/Huston Rockets/Cleveland Cavaliers/2025-26")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Stats not found for this team and this rival in this season"}

@pytest.mark.asyncio
async def test_show_player_stats_against_team(test_data_player_logs, test_data_players, test_data_teams):
    respons = client.get("/user/show-player-stats-against-team/Kevin Durant/Los Angeles Lakers/2025-26")
    assert respons.status_code == status.HTTP_200_OK
    assert respons.json() == {"avg_points" : 34.0,
                            "avg_minutes_played" : 30.0,
                            "avg_assists" : 3.0,  
                            "avg_blocks" : 3.0, 
                            "avg_steals" : 1.0,
                            "avg_turnovers" : 2.0,
                            "avg_rebounds" : 8.0,
                            "avg_offensive_rebounds" : 5.0,
                            "avg_defensive_rebounds" : 3.0,
                            "avg_personal_fouls" : 1.0,
                            "avg_personal_fouls_drawn" : 1.0,
                            "avg_field_goals_made" : 15.0,
                            "avg_field_goals_attempted" : 20.0,
                            "avg_field_goal_percentage" : 80.0,
                            "avg_three_point_field_goals_made" : 2.0,
                            "avg_three_point_field_goals_attempted" : 4.0,
                            "avg_three_point_field_goal_percentage" : 50.0,
                            "avg_free_throws_made" : 4.0,
                            "avg_free_throws_attempted" : 4.0,
                            "avg_free_throw_percentage" : 100.0}

@pytest.mark.asyncio
async def test_show_player_stats_against_team_if_player_not_exist(test_data_player_logs, test_data_players, test_data_teams):
    respons = client.get("/user/show-player-stats-against-team/Kevin /Los Angeles Lakers/2025-26")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Player is not exists"}

@pytest.mark.asyncio
async def test_show_player_stats_against_team_if_team_is_not_exist(test_data_player_logs, test_data_players, test_data_teams):
    respons = client.get("/user/show-player-stats-against-team/Kevin Durant/Los Lakers/2025-26")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Team is not exists"}

@pytest.mark.asyncio
async def test_show_player_stats_against_team_if_season_is_not_exist(test_data_player_logs, test_data_players, test_data_teams):
    respons = client.get("/user/show-player-stats-against-team/Kevin Durant/Los Angeles Lakers/2028-29")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Season is not exist or will start soon"}

@pytest.mark.asyncio
async def test_show_player_stats_against_team_if_player_is_not_played_against_team(test_data_player_logs, test_data_players, test_data_teams):
    respons = client.get("/user/show-player-stats-against-team/Kevin Durant/Cleveland Cavaliers/2025-26")
    assert respons.status_code == status.HTTP_400_BAD_REQUEST
    assert respons.json() == {"detail" : "Stats not found for this player and this rival in this season"}