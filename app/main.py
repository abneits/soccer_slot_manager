from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from typing import Optional
from dotenv import load_dotenv
import os
import secrets
from jinja2 import Environment, FileSystemLoader

from app.models import (
    Slot, 
    PlayerRegistration, 
    SlotResponse,
    User,
    UserInDB,
    InvitationToken,
    UserRegistration,
    LoginRequest,
    LoginResponse,
    InviteTokenResponse,
    UserUpdateRequest,
    GuestRegistration
)

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

# Add new collection names
USERS_COLLECTION = "Users"
INVITATIONS_COLLECTION = "InvitationTokens"


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

# Configure Jinja2 with custom delimiters to avoid conflict with Vue.js
class CustomJinja2Templates(Jinja2Templates):
    def _create_env(self, directory, **env_options):
        loader = FileSystemLoader(directory)
        env = Environment(
            loader=loader,
            variable_start_string='{[',
            variable_end_string=']}',
            block_start_string='{%',
            block_end_string='%}',
            **env_options
        )
        return env

templates = CustomJinja2Templates(directory="app/templates")


def get_db():
    """Get database instance"""
    return db_client[DB_NAME]


def get_collection():
    """Get slots collection"""
    return get_db()[COLLECTION_NAME]


def get_users_collection():
    """Get users collection"""
    return get_db()[USERS_COLLECTION]


def get_invitations_collection():
    """Get invitations collection"""
    return get_db()[INVITATIONS_COLLECTION]


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


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


# Authentication Endpoints

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    users = get_users_collection()
    user = await users.find_one({"username": request.username, "pin": request.pin})
    
    if not user:
        return LoginResponse(success=False, message="Nom d'utilisateur ou code PIN incorrect")
    
    return LoginResponse(
        success=True,
        user={
            "username": user["username"],
            "role": user["role"]
        },
        message="Connexion réussie"
    )

@app.post("/api/auth/signup")
async def signup(registration: UserRegistration):
    users = get_users_collection()
    invitations = get_invitations_collection()
    
    # Validate PIN format
    if len(registration.pin) != 4 or not registration.pin.isdigit():
        raise HTTPException(status_code=400, detail="Le code PIN doit contenir exactement 4 chiffres")
    
    # Check if username already exists
    existing_user = await users.find_one({"username": registration.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")
    
    # Validate invitation token
    token_doc = await invitations.find_one({"token": registration.inviteToken})
    if not token_doc:
        raise HTTPException(status_code=400, detail="Code d'invitation invalide")
    
    if datetime.now(timezone.utc) > token_doc["expiresAt"]:
        raise HTTPException(status_code=400, detail="Ce code d'invitation a expiré")
    
    # Create user
    new_user = {
        "username": registration.username,
        "pin": registration.pin,
        "role": "user",
        "invitedBy": token_doc["createdBy"]
    }
    
    await users.insert_one(new_user)
    
    # Delete used token
    await invitations.delete_one({"token": registration.inviteToken})
    
    return {"success": True, "message": "Compte créé avec succès"}


# Admin Endpoints

@app.get("/api/admin/users")
async def get_all_users(admin_username: str):
    users = get_users_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    user_list = []
    async for user in users.find({}):
        user_list.append({
            "id": str(user["_id"]),
            "username": user["username"],
            "role": user["role"],
            "invitedBy": user.get("invitedBy")
        })
    
    return user_list

@app.put("/api/admin/users/{user_id}")
async def update_user(user_id: str, update: UserUpdateRequest, admin_username: str):
    users = get_users_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Check if new username already exists
    existing = await users.find_one({"username": update.username, "_id": {"$ne": ObjectId(user_id)}})
    if existing:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")
    
    result = await users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"username": update.username}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {"success": True}

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str, admin_username: str):
    users = get_users_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    result = await users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {"success": True}

@app.post("/api/admin/users/{user_id}/reset-pin")
async def reset_user_pin(user_id: str, admin_username: str):
    users = get_users_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    result = await users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"pin": "0000"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {"success": True, "message": "Code PIN réinitialisé à 0000"}

@app.post("/api/admin/generate-invite", response_model=InviteTokenResponse)
async def generate_invite_token(admin_username: str):
    users = get_users_collection()
    invitations = get_invitations_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Generate token
    token = secrets.token_urlsafe(16)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    invitation = {
        "token": token,
        "createdBy": admin_username,
        "expiresAt": expires_at
    }
    
    await invitations.insert_one(invitation)
    
    return InviteTokenResponse(token=token, expiresAt=expires_at)


# Update slot registration endpoints

@app.post("/api/register", response_model=SlotResponse)
async def register_player(registration: PlayerRegistration, username: str):
    # Verify user is authenticated
    users = get_users_collection()
    user = await users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    collection = get_collection()
    target_date = get_next_wednesday_at_19()
    
    slot = await collection.find_one({"date": target_date})
    
    if not slot:
        slot = {
            "date": target_date,
            "players": [],
            "is_full": False
        }
        await collection.insert_one(slot)
    
    if slot.get("is_full"):
        raise HTTPException(status_code=400, detail="Le créneau est complet")
    
    # Check if user already registered
    if username in slot["players"]:
        raise HTTPException(status_code=400, detail="Vous êtes déjà inscrit")
    
    if len(slot["players"]) >= MAX_PLAYERS:
        await collection.update_one(
            {"date": target_date},
            {"$set": {"is_full": True}}
        )
        raise HTTPException(status_code=400, detail="Le créneau est complet")
    
    # Register user
    await collection.update_one(
        {"date": target_date},
        {"$push": {"players": username}}
    )
    
    updated_slot = await collection.find_one({"date": target_date})
    
    if len(updated_slot["players"]) >= MAX_PLAYERS:
        await collection.update_one(
            {"date": target_date},
            {"$set": {"is_full": True}}
        )
        updated_slot["is_full"] = True
    
    return SlotResponse(
        date=updated_slot["date"].isoformat(),
        players=updated_slot["players"],
        player_count=len(updated_slot["players"]),
        max_players=MAX_PLAYERS
    )

@app.post("/api/register-guest", response_model=SlotResponse)
async def register_guest(guest: GuestRegistration, username: str):
    users = get_users_collection()
    user = await users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    collection = get_collection()
    target_date = get_next_wednesday_at_19()
    
    slot = await collection.find_one({"date": target_date})
    
    if not slot:
        slot = {
            "date": target_date,
            "players": [],
            "is_full": False
        }
        await collection.insert_one(slot)
    
    if slot.get("is_full"):
        raise HTTPException(status_code=400, detail="Le créneau est complet")
    
    if len(slot["players"]) >= MAX_PLAYERS:
        await collection.update_one(
            {"date": target_date},
            {"$set": {"is_full": True}}
        )
        raise HTTPException(status_code=400, detail="Le créneau est complet")
    
    # Format guest name
    guest_display_name = f"(Invité) {guest.guestName} [par {username}]"
    
    await collection.update_one(
        {"date": target_date},
        {"$push": {"players": guest_display_name}}
    )
    
    updated_slot = await collection.find_one({"date": target_date})
    
    if len(updated_slot["players"]) >= MAX_PLAYERS:
        await collection.update_one(
            {"date": target_date},
            {"$set": {"is_full": True}}
        )
        updated_slot["is_full"] = True
    
    return SlotResponse(
        date=updated_slot["date"].isoformat(),
        players=updated_slot["players"],
        player_count=len(updated_slot["players"]),
        max_players=MAX_PLAYERS
    )

@app.delete("/api/unregister/{player_name}")
async def unregister_player(player_name: str, username: str):
    users = get_users_collection()
    user = await users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    collection = get_collection()
    target_date = get_next_wednesday_at_19()
    
    slot = await collection.find_one({"date": target_date})
    
    if not slot:
        raise HTTPException(status_code=404, detail="Créneau non trouvé")
    
    # Check permissions
    is_admin = user["role"] == "admin"
    is_own_registration = player_name == username
    is_own_guest = f"[par {username}]" in player_name
    
    if not (is_admin or is_own_registration or is_own_guest):
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas supprimer cette inscription")
    
    if player_name not in slot["players"]:
        raise HTTPException(status_code=404, detail="Joueur non trouvé")
    
    await collection.update_one(
        {"date": target_date},
        {"$pull": {"players": player_name}, "$set": {"is_full": False}}
    )
    
    updated_slot = await collection.find_one({"date": target_date})
    
    return SlotResponse(
        date=updated_slot["date"].isoformat(),
        players=updated_slot["players"],
        player_count=len(updated_slot["players"]),
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
