from sqlalchemy import ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    name : Mapped[str] 
    last_name : Mapped[str]
    username : Mapped[str] = mapped_column(unique = True)
    password : Mapped[str]
    email : Mapped[str]
    role : Mapped[str] = mapped_column(Enum("user", "admin", name = "enum_name"), default = "user")
    user_status  : Mapped[bool]

class Teams(Base):
    __tablename__ = "nba_teams"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    team_id : Mapped[int] = mapped_column(unique = True)
    team_name : Mapped[str]
    abbreviation : Mapped[str]

class Players(Base):
    __tablename__ = "nba_players"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    player_id : Mapped[int] = mapped_column(unique = True)
    player_name : Mapped[str]
    player_last_name : Mapped[str]
    player_team : Mapped[int] = mapped_column(ForeignKey("nba_teams.id"), nullable = True)
    is_active : Mapped[bool]

class UserFavoritePlayer(Base):
    __tablename__ = "user_favorite_player"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id"))
    player_id : Mapped[int] = mapped_column(ForeignKey("nba_players.id"))

class UserFavoriteTeam(Base):
    __tablename__ = "user_favorite_teams"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id"))
    team_id : Mapped[int] = mapped_column(ForeignKey("nba_teams.id"))

class PlayersGameLogs(Base):
    __tablename__ = "players_game_logs"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    season : Mapped[str]
    player_id : Mapped[int] = mapped_column(ForeignKey("nba_players.player_id"))
    team_id : Mapped[int] = mapped_column(ForeignKey("nba_teams.team_id"))
    game_id : Mapped[str]
    game_date : Mapped[datetime]
    matchup : Mapped[str]
    is_win : Mapped[bool]
    minutes_played : Mapped[float]
    field_goals_made : Mapped[int]
    field_goals_attempted: Mapped[int]
    field_goal_percentage: Mapped[float]
    three_point_field_goals_made : Mapped[int]
    three_point_field_goals_attempted : Mapped[int]
    three_point_field_goal_percentage : Mapped[float]
    free_throws_made : Mapped[int]
    free_throws_attempted : Mapped[int]
    free_throw_percentage : Mapped[float]
    offensive_rebounds : Mapped[int]
    defensive_rebounds : Mapped[int]
    rebounds : Mapped[int]
    assists : Mapped[int]
    turnovers : Mapped[int]
    steals : Mapped[int]
    blocks : Mapped[int]
    blocks_against : Mapped[int]
    personal_fouls : Mapped[int]
    personal_fouls_drawn : Mapped[int]
    points : Mapped[int]

class TeamsGameLogs(Base):
    __tablename__ = "teams_game_logs"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    season : Mapped[str]
    team_id : Mapped[int] = mapped_column(ForeignKey("nba_teams.team_id"))
    game_id : Mapped[str] 
    game_date : Mapped[datetime]
    matchup : Mapped[str]
    is_win : Mapped[bool]
    field_goals_made : Mapped[int]
    field_goals_attempted: Mapped[int]
    field_goal_percentage: Mapped[float]
    three_point_field_goals_made : Mapped[int]
    three_point_field_goals_attempted : Mapped[int]
    three_point_field_goal_percentage : Mapped[float]
    free_throws_made : Mapped[int]
    free_throws_attempted : Mapped[int]
    free_throw_percentage : Mapped[float]
    offensive_rebounds : Mapped[int]
    defensive_rebounds : Mapped[int]
    rebounds : Mapped[int]
    assists : Mapped[int]
    turnovers : Mapped[int]
    steals : Mapped[int]
    blocks : Mapped[int]
    blocks_against : Mapped[int]
    personal_fouls : Mapped[int]
    personal_fouls_drawn : Mapped[int]
    points : Mapped[int]

class StatusTLog(Base):
    __tablename__ = "status_log"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    log_description : Mapped[str]
    downloaded_records : Mapped[int]
    date : Mapped[datetime] = mapped_column(DateTime, default = func.now())
    completed : Mapped[bool]
    log_type : Mapped[str] = mapped_column(Enum("players_log", "teams_log", "teams_list", "players_list", name ="log_type_enum"))