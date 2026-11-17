from pydantic import BaseModel, Field

class UserChangeInformationRequest(BaseModel):
    name : str
    last_name : str
    username : str
    email : str

class PasswordRequest(BaseModel):
    old_password : str
    new_password : str

class DeleteUserRequest(BaseModel):
    password : str = Field(description = "Pass password to confirm that you want to delete account")

class SuccessMessageRespond(BaseModel):
    message : str

class UserInformationResponse(BaseModel):
    name: str
    last_name : str
    username : str
    email : str
    role : str