from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime


class Slot(BaseModel):
    """MongoDB Slot Document Model"""
    date: datetime = Field(..., description="ISO Date for the Wednesday at 19:00")
    players: List[str] = Field(default_factory=list, description="List of player names")
    teamA: List[str] = Field(default_factory=list, description="Team A player IDs (max 5)")
    teamB: List[str] = Field(default_factory=list, description="Team B player IDs (max 5)")
    teamAScore: Optional[int] = Field(default=None, description="Team A score")
    teamBScore: Optional[int] = Field(default=None, description="Team B score")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-12-10T19:00:00",
                "players": ["Alice", "Bob", "Charlie"],
                "teamA": [],
                "teamB": [],
                "teamAScore": None,
                "teamBScore": None
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
    timestamps: List[str] = Field(default_factory=list, description="Registration timestamps in ISO format")
    teamA: List[dict] = Field(default_factory=list, description="Team A composition with player details")
    teamB: List[dict] = Field(default_factory=list, description="Team B composition with player details")
    teamAScore: Optional[int] = Field(default=None, description="Team A score")
    teamBScore: Optional[int] = Field(default=None, description="Team B score")
    isRegistrationOpen: bool = Field(default=True, description="Whether registration is currently allowed")


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


class TeamComposition(BaseModel):
    """Request model for setting team composition"""
    teamA: List[str] = Field(..., max_length=5, description="Team A player IDs (max 5)")
    teamB: List[str] = Field(..., max_length=5, description="Team B player IDs (max 5)")


class TeamScores(BaseModel):
    """Request model for updating team scores"""
    teamAScore: int = Field(..., ge=0, description="Team A score")
    teamBScore: int = Field(..., ge=0, description="Team B score")
