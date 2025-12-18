from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from bson import ObjectId
from typing import Optional
from dotenv import load_dotenv
import os
import random
from jinja2 import Environment, FileSystemLoader

from app.models import (
    Slot, 
    PlayerRegistration, 
    SlotResponse,
    UserRegistration,
    LoginRequest,
    LoginResponse,
    InviteTokenResponse,
    GuestRegistration
)

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "Soccer-manager"
COLLECTION_NAME = "Slots"
USERS_COLLECTION = "Users"
INVITATIONS_COLLECTION = "InvitationTokens"

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


# =============================================================================
# FRONTEND ROUTES
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Serve the admin dashboard page"""
    return templates.TemplateResponse("admin.html", {"request": request})


# =============================================================================
# SLOT MANAGEMENT ENDPOINTS
# =============================================================================

@app.get("/api/current-slot", response_model=SlotResponse)
async def get_current_slot():
    """
    Get or create the current slot for the next Wednesday at 19:00.
    
    Returns:
        SlotResponse: Current slot data including date, players, and status
    """
    collection = get_collection()
    target_date = get_next_wednesday_at_19()
    
    # Check if slot exists for this date
    slot_doc = await collection.find_one({"date": target_date})
    
    if not slot_doc:
        # Create new slot with new structure (players array with references, guests array)
        new_slot = {
            "date": target_date,
            "players": [],
            "guests": []
        }
        await collection.insert_one(new_slot)
        slot_doc = new_slot
    
    # Format response: combine players and guests for display
    players_list = [p["username"] for p in slot_doc.get("players", [])]
    guests_list = [f"(Invité) {g['name']} [par {g['invitedBy']}]" for g in slot_doc.get("guests", [])]
    all_players = players_list + guests_list
    
    return SlotResponse(
        date=slot_doc["date"].isoformat(),
        players=all_players,
        player_count=len(all_players),
        max_players=MAX_PLAYERS
    )


@app.post("/api/register", response_model=SlotResponse)
async def register_player(registration: PlayerRegistration, username: str):
    """Register authenticated user to the current slot"""
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
            "guests": []
        }
        await collection.insert_one(slot)
    
    # Check total capacity (players + guests)
    total_registered = len(slot.get("players", [])) + len(slot.get("guests", []))
    
    if total_registered >= MAX_PLAYERS:
        raise HTTPException(status_code=400, detail="Le créneau est complet")
    
    # Check if user already registered
    player_ids = [p["user_id"] for p in slot.get("players", [])]
    if str(user["_id"]) in player_ids:
        raise HTTPException(status_code=400, detail="Vous êtes déjà inscrit")
    
    # Register user with reference (store user_id and username)
    await collection.update_one(
        {"date": target_date},
        {"$push": {"players": {
            "user_id": str(user["_id"]),
            "username": username
        }}}
    )
    
    updated_slot = await collection.find_one({"date": target_date})
    total_registered = len(updated_slot.get("players", [])) + len(updated_slot.get("guests", []))
    
    # Format response for frontend
    players_list = [p["username"] for p in updated_slot.get("players", [])]
    guests_list = [f"(Invité) {g['name']} [par {g['invitedBy']}]" for g in updated_slot.get("guests", [])]
    
    return SlotResponse(
        date=updated_slot["date"].isoformat(),
        players=players_list + guests_list,
        player_count=total_registered,
        max_players=MAX_PLAYERS
    )


@app.post("/api/register-guest", response_model=SlotResponse)
async def register_guest(guest: GuestRegistration, username: str):
    """Register a guest player (added by authenticated user)"""
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
            "guests": []
        }
        await collection.insert_one(slot)
    
    # Check total capacity
    total_registered = len(slot.get("players", [])) + len(slot.get("guests", []))
    
    if total_registered >= MAX_PLAYERS:
        raise HTTPException(status_code=400, detail="Le créneau est complet")
    
    # Check if guest name already exists (global check)
    existing_guests = [g["name"] for g in slot.get("guests", [])]
    if guest.guestName in existing_guests:
        raise HTTPException(status_code=400, detail="Un invité avec ce nom est déjà inscrit")
    
    # Add guest with invitator reference
    await collection.update_one(
        {"date": target_date},
        {"$push": {"guests": {
            "name": guest.guestName,
            "invitedBy_id": str(user["_id"]),
            "invitedBy": username
        }}}
    )
    
    updated_slot = await collection.find_one({"date": target_date})
    total_registered = len(updated_slot.get("players", [])) + len(updated_slot.get("guests", []))
    
    # Format response for frontend
    players_list = [p["username"] for p in updated_slot.get("players", [])]
    guests_list = [f"(Invité) {g['name']} [par {g['invitedBy']}]" for g in updated_slot.get("guests", [])]
    
    return SlotResponse(
        date=updated_slot["date"].isoformat(),
        players=players_list + guests_list,
        player_count=total_registered,
        max_players=MAX_PLAYERS
    )


@app.delete("/api/unregister/{player_name}")
async def unregister_player(player_name: str, username: str):
    """Remove a player or guest from the current slot"""
    users = get_users_collection()
    user = await users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    
    collection = get_collection()
    target_date = get_next_wednesday_at_19()
    
    slot = await collection.find_one({"date": target_date})
    if not slot:
        raise HTTPException(status_code=404, detail="Créneau non trouvé")
    
    is_admin = user["role"] == "admin"
    player_found = False
    
    # Try to remove from players array
    for player in slot.get("players", []):
        if player["username"] == player_name:
            if is_admin or player["user_id"] == str(user["_id"]):
                await collection.update_one(
                    {"date": target_date},
                    {"$pull": {"players": {"username": player_name}}}
                )
                player_found = True
                break
            else:
                raise HTTPException(status_code=403, detail="Vous ne pouvez pas supprimer cette inscription")
    
    # Try to remove from guests array if not found in players
    if not player_found and player_name.startswith("(Invité)"):
        # Extract guest name from format "(Invité) Name [par username]"
        try:
            guest_name = player_name.split("(Invité) ")[1].split(" [par ")[0]
        except IndexError:
            raise HTTPException(status_code=404, detail="Format de nom d'invité invalide")
        
        for guest in slot.get("guests", []):
            if guest["name"] == guest_name:
                if is_admin or guest.get("invitedBy_id") == str(user["_id"]):
                    await collection.update_one(
                        {"date": target_date},
                        {"$pull": {"guests": {"name": guest_name}}}
                    )
                    player_found = True
                    break
                else:
                    raise HTTPException(status_code=403, detail="Vous ne pouvez pas supprimer cette inscription")
    
    if not player_found:
        raise HTTPException(status_code=404, detail="Joueur non trouvé")
    
    updated_slot = await collection.find_one({"date": target_date})
    total_registered = len(updated_slot.get("players", [])) + len(updated_slot.get("guests", []))
    
    # Format response for frontend
    players_list = [p["username"] for p in updated_slot.get("players", [])]
    guests_list = [f"(Invité) {g['name']} [par {g['invitedBy']}]" for g in updated_slot.get("guests", [])]
    
    return SlotResponse(
        date=updated_slot["date"].isoformat(),
        players=players_list + guests_list,
        player_count=total_registered,
        max_players=MAX_PLAYERS
    )


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user with username and PIN"""
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
    """Create new user account with invitation token"""
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
    
    # Check token expiration (MongoDB stores naive datetime)
    if datetime.now() > token_doc["expiresAt"]:
        raise HTTPException(status_code=400, detail="Ce code d'invitation a expiré")
    
    # Get admin who created the token (store reference, not just username)
    admin = await users.find_one({"username": token_doc["createdBy"]})
    
    # Create user with admin reference who invited
    new_user = {
        "username": registration.username,
        "pin": registration.pin,
        "role": "user",
        "invitedBy": str(admin["_id"]) if admin else None   # Reference to admin who invited
    }
    
    await users.insert_one(new_user)
    
    # DELETE used token from database
    await invitations.delete_one({"token": registration.inviteToken})
    
    return {"success": True, "message": "Compte créé avec succès"}


@app.post("/api/auth/change-pin")
async def change_pin(username: str, old_pin: str, new_pin: str):
    """Allow user to change their PIN"""
    users = get_users_collection()
    
    # Validate new PIN format
    if len(new_pin) != 4 or not new_pin.isdigit():
        raise HTTPException(status_code=400, detail="Le nouveau code PIN doit contenir exactement 4 chiffres")
    
    # Verify current credentials
    user = await users.find_one({"username": username, "pin": old_pin})
    if not user:
        raise HTTPException(status_code=403, detail="Code PIN actuel incorrect")
    
    # Update PIN
    result = await users.update_one(
        {"_id": user["_id"]},
        {"$set": {"pin": new_pin}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour")
    
    return {"success": True, "message": "Code PIN modifié avec succès"}


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@app.get("/api/admin/users")
async def get_all_users(admin_username: str):
    """Get list of all users (admin only)"""
    users = get_users_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    user_list = []
    async for user in users.find({}):
        # Get invitor username if invitedBy exists
        invitor_name = None
        if user.get("invitedBy"):
            invitor = await users.find_one({"_id": ObjectId(user["invitedBy"])})
            invitor_name = invitor["username"] if invitor else None
        
        user_list.append({
            "id": str(user["_id"]),
            "username": user["username"],
            "role": user["role"],
            "invitedBy": invitor_name
        })
    
    return user_list


@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str, admin_username: str):
    """Delete a user account (admin only)"""
    users = get_users_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    result = await users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {"success": True}


@app.post("/api/admin/generate-invite", response_model=InviteTokenResponse)
async def generate_invite_token(admin_username: str):
    """Generate 6-digit invitation token (admin only)"""
    users = get_users_collection()
    invitations = get_invitations_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Generate 6-digit numeric token
    token = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    expires_at = datetime.now() + timedelta(hours=24)
    
    invitation = {
        "token": token,
        "createdBy": admin_username,
        "expiresAt": expires_at
    }
    
    await invitations.insert_one(invitation)
    
    return InviteTokenResponse(token=token, expiresAt=expires_at)


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
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
