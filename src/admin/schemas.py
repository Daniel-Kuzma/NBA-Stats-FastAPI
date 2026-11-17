from pydantic import BaseModel
from enum import Enum
from datetime import datetime
import uuid

class UserRoleEnum(str, Enum):
    admin = "admin"
    user = "user"

class SuccessMessageRespond(BaseModel):
    message : str

class AllUsersRespond(BaseModel):
    public_id : uuid.UUID
    name : str
    last_name : str
    username : str
    email : str
    role : str
    user_status : bool

class DataLogsRespond(BaseModel):
    log_description : str
    downloaded_records : int
    date : datetime
    completed : bool
    log_type : str