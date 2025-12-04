from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv

from app.models import Slot, PlayerRegistration, SlotResponse

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "Soccer-manager"
COLLECTION_NAME = "Slots"

# Constants
MAX_PLAYERS = 10
MATCH_HOUR = 19
MATCH_MINUTE = 0
MATCH_DAY = 2  # Wednesday (0=Monday, 6=Sunday)


# Global database client
db_client: Optional[AsyncIOMotorClient] = None


def get_next_wednesday_at_19() -> datetime:
    """
    Calculate the next Wednesday at 19:00.
    
    Business Logic:
    - If today is Wednesday and current time is before 19:00, return today at 19:00
    - Otherwise, return next Wednesday at 19:00
    """
    now = datetime.now()
    current_weekday = now.weekday()
    
    # If it's Wednesday (2) and before 19:00
    if current_weekday == MATCH_DAY and now.hour < MATCH_HOUR:
        target_date = now.replace(hour=MATCH_HOUR, minute=MATCH_MINUTE, second=0, microsecond=0)
    else:
        # Calculate days until next Wednesday
        days_ahead = MATCH_DAY - current_weekday
        if days_ahead <= 0:  # Target day already passed this week
            days_ahead += 7
        
        target_date = now + timedelta(days=days_ahead)
        target_date = target_date.replace(hour=MATCH_HOUR, minute=MATCH_MINUTE, second=0, microsecond=0)
    
    return target_date


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for MongoDB connection.
    Handles startup and shutdown of database connection.
    """
    global db_client
    
    # Startup: Connect to MongoDB
    print(f"🔌 Connecting to MongoDB...")
    db_client = AsyncIOMotorClient(MONGO_URI)
    
    # Verify connection
    try:
        await db_client.admin.command('ping')
        print(f"✅ Successfully connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise
    
    yield
    
    # Shutdown: Close MongoDB connection
    print("🔌 Closing MongoDB connection...")
    db_client.close()
    print("✅ MongoDB connection closed")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Soccer Slot Manager",
    description="Lightweight web application to manage indoor soccer slot reservations",
    version="1.0.0",
    lifespan=lifespan
)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


def get_db():
    """Get database instance"""
    return db_client[DB_NAME]


def get_collection():
    """Get slots collection"""
    return get_db()[COLLECTION_NAME]


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/current-slot", response_model=SlotResponse)
async def get_current_slot():
    """
    Get or create the current slot for the next Wednesday at 19:00.
    
    Returns:
        SlotResponse: Current slot data including date, players, and status
    """
    collection = get_collection()
    
    # Calculate next Wednesday date
    target_date = get_next_wednesday_at_19()
    
    # Check if slot exists for this date
    slot_doc = await collection.find_one({"date": target_date})
    
    if not slot_doc:
        # Create new slot
        new_slot = Slot(
            date=target_date,
            players=[]
        )
        
        await collection.insert_one(new_slot.model_dump())
        slot_doc = new_slot.model_dump()
    
    # Prepare response
    return SlotResponse(
        date=slot_doc["date"].isoformat(),
        players=slot_doc["players"],
        player_count=len(slot_doc["players"]),
        max_players=MAX_PLAYERS
    )


@app.post("/api/register", response_model=SlotResponse)
async def register_player(registration: PlayerRegistration):
    """
    Register a player for the current slot.
    
    Args:
        registration: PlayerRegistration with player name
        
    Returns:
        SlotResponse: Updated slot data
        
    Raises:
        HTTPException: If slot is full or player already registered
    """
    collection = get_collection()
    
    # Calculate next Wednesday date
    target_date = get_next_wednesday_at_19()
    
    # Get current slot
    slot_doc = await collection.find_one({"date": target_date})
    
    if not slot_doc:
        # Create slot if it doesn't exist
        new_slot = Slot(
            date=target_date,
            players=[]
        )
        await collection.insert_one(new_slot.model_dump())
        slot_doc = new_slot.model_dump()
    
    # Check if slot is full (based on player count)
    if len(slot_doc["players"]) >= MAX_PLAYERS:
        raise HTTPException(
            status_code=400,
            detail="Slot is full. Maximum 10 players allowed."
        )
    
    # Check if player already registered
    player_name = registration.name
    if player_name in slot_doc["players"]:
        raise HTTPException(
            status_code=400,
            detail=f"Player '{player_name}' is already registered."
        )
    
    # Add player to slot
    updated_players = slot_doc["players"] + [player_name]
    
    # Update database
    await collection.update_one(
        {"date": target_date},
        {
            "$set": {
                "players": updated_players
            }
        }
    )
    
    # Return updated slot
    return SlotResponse(
        date=target_date.isoformat(),
        players=updated_players,
        player_count=len(updated_players),
        max_players=MAX_PLAYERS
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Ping database
        await db_client.admin.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
