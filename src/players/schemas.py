from pydantic import BaseModel

class SuccessfullyMessageRespond(BaseModel):
    message : str

class AllUserFavoritePlayersResponse(BaseModel):
    display_name : str
    team_name : str
    avg_points : float
    avg_assist : float
    avg_steals : float

class AllUserFavoriteTeamResponse(BaseModel):
    team_name : str
    avg_points : float
    avg_assists : float
    avg_steals : float

class StatsRespons(BaseModel):
    avg_points : float
    avg_assists : float
    avg_blocks : float
    avg_steals : float
    avg_turnovers : float
    avg_rebounds : float
    avg_offensive_rebounds : float
    avg_defensive_rebounds : float
    avg_personal_fouls : float
    avg_personal_fouls_drawn : float
    avg_field_goals_made : float
    avg_field_goals_attempted : float
    avg_field_goal_percentage : float
    avg_three_point_field_goals_made : float
    avg_three_point_field_goals_attempted : float
    avg_three_point_field_goal_percentage : float
    avg_free_throws_made : float
    avg_free_throws_attempted : float
    avg_free_throw_percentage : float

class PlayerStatsRespons(BaseModel):
    avg_points : float
    avg_minutes_played : float
    avg_assists : float
    avg_blocks : float
    avg_steals : float
    avg_turnovers : float
    avg_rebounds : float
    avg_offensive_rebounds : float
    avg_defensive_rebounds : float
    avg_personal_fouls : float
    avg_personal_fouls_drawn : float
    avg_field_goals_made : float
    avg_field_goals_attempted : float
    avg_field_goal_percentage : float
    avg_three_point_field_goals_made : float
    avg_three_point_field_goals_attempted : float
    avg_three_point_field_goal_percentage : float
    avg_free_throws_made : float
    avg_free_throws_attempted : float
    avg_free_throw_percentage : float

