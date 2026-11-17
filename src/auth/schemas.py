from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token : str
    token_type : str 

class LoginInRequest(BaseModel):
    username : str
    password : str

class RequestUser(BaseModel):
    name : str = Field(min_length = 1)
    last_name : str = Field(min_length = 1)
    username : str = Field(min_length = 3, max_length = 30)
    password : str = Field(min_length = 8)
    email : str = Field(min_length = 3)
    role : str = Field(default = "user")

class SuccessMessageResponse(BaseModel):
    message : str