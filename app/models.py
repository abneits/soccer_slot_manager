from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime


class Slot(BaseModel):
    """MongoDB Slot Document Model"""
    date: datetime = Field(..., description="ISO Date for the Wednesday at 19:00")
    players: List[str] = Field(default_factory=list, description="List of player names")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-12-10T19:00:00",
                "players": ["Alice", "Bob", "Charlie"]
            }
        }


class PlayerRegistration(BaseModel):
    """Request model for player registration"""
    name: str = Field(..., min_length=1, max_length=100, description="Player name")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that name is not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError("Player name cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe"
            }
        }


class SlotResponse(BaseModel):
    """Response model for slot data"""
    date: str = Field(..., description="ISO formatted date string")
    players: List[str] = Field(..., description="List of player names")
    player_count: int = Field(..., description="Current number of players")
    max_players: int = Field(default=10, description="Maximum allowed players")


class User(BaseModel):
    username: str
    pin: str  # 4 digits, stored in plain text
    role: Literal['user', 'admin']
    invitedBy: Optional[str] = None  # username of inviter


class UserInDB(User):
    id: str = Field(alias="_id")


class InvitationToken(BaseModel):
    token: str
    createdBy: str  # admin username
    expiresAt: datetime


class UserRegistration(BaseModel):
    username: str
    pin: str
    inviteToken: str


class LoginRequest(BaseModel):
    username: str
    pin: str


class LoginResponse(BaseModel):
    success: bool
    user: Optional[dict] = None
    message: str


class InviteTokenResponse(BaseModel):
    token: str
    expiresAt: datetime


class UserUpdateRequest(BaseModel):
    username: str


class GuestRegistration(BaseModel):
    guestName: str


class ChangePinRequest(BaseModel):
    old_pin: str
    new_pin: str
