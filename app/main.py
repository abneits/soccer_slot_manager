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
import random
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
    GuestRegistration,
    ChangePinRequest
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


    """Get database instance"""""
    return db_client[DB_NAME]    return db_client[DB_NAME]


def get_collection():
    """Get slots collection"""
    return get_db()[COLLECTION_NAME]    return get_db()[COLLECTION_NAME]


def get_users_collection():
    """Get users collection"""
    return get_db()[USERS_COLLECTION]    return get_db()[USERS_COLLECTION]


def get_invitations_collection():
    """Get invitations collection"""
    return get_db()[INVITATIONS_COLLECTION]    return get_db()[INVITATIONS_COLLECTION]


@app.get("/", response_class=HTMLResponse)nse)
async def read_root(request: Request):st):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)esponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/api/current-slot", response_model=SlotResponse) response_model=SlotResponse)
async def get_current_slot():ef get_current_slot():
    """
    Get or create the current slot for the next Wednesday at 19:00.Get or create the current slot for the next Wednesday at 19:00.
    
    Returns:
        SlotResponse: Current slot data including date, players, and status SlotResponse: Current slot data including date, players, and status
    """
    collection = get_collection()collection = get_collection()
    
    # Calculate next Wednesday date
    target_date = get_next_wednesday_at_19()target_date = get_next_wednesday_at_19()
    
    # Check if slot exists for this date
    slot_doc = await collection.find_one({"date": target_date})slot_doc = await collection.find_one({"date": target_date})
    
    if not slot_doc:
        # Create new slott
        new_slot = Slot(
            date=target_date,t_date,
            players=[]   players=[]
        ))
        
        await collection.insert_one(new_slot.model_dump())slot.model_dump())
        slot_doc = new_slot.model_dump()    slot_doc = new_slot.model_dump()
    
    # Prepare response
    return SlotResponse(
        date=slot_doc["date"].isoformat(),mat(),
        players=slot_doc["players"],
        player_count=len(slot_doc["players"]),oc["players"]),
        max_players=MAX_PLAYERS   max_players=MAX_PLAYERS
    )    )


# Authentication Endpoints# Authentication Endpoints

@app.post("/api/auth/login", response_model=LoginResponse)odel=LoginResponse)
async def login(request: LoginRequest):est):
    users = get_users_collection()
    user = await users.find_one({"username": request.username, "pin": request.pin})user = await users.find_one({"username": request.username, "pin": request.pin})
    
    if not user:
        return LoginResponse(success=False, message="Nom d'utilisateur ou code PIN incorrect")    return LoginResponse(success=False, message="Nom d'utilisateur ou code PIN incorrect")
    
    return LoginResponse(nse(
        success=True,s=True,
        user={
            "username": user["username"],ername"],
            "role": user["role"]  "role": user["role"]
        },
        message="Connexion réussie"   message="Connexion réussie"
    )    )

@app.post("/api/auth/signup")
async def signup(registration: UserRegistration):rRegistration):
    users = get_users_collection()
    invitations = get_invitations_collection()invitations = get_invitations_collection()
    
    # Validate PIN format
    if len(registration.pin) != 4 or not registration.pin.isdigit():
        raise HTTPException(status_code=400, detail="Le code PIN doit contenir exactement 4 chiffres")    raise HTTPException(status_code=400, detail="Le code PIN doit contenir exactement 4 chiffres")
    
    # Check if username already exists
    existing_user = await users.find_one({"username": registration.username})wait users.find_one({"username": registration.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")    raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")
    
    # Validate invitation token
    token_doc = await invitations.find_one({"token": registration.inviteToken}) invitations.find_one({"token": registration.inviteToken})
    if not token_doc:
        raise HTTPException(status_code=400, detail="Code d'invitation invalide")    raise HTTPException(status_code=400, detail="Code d'invitation invalide")
    
    if datetime.now(timezone.utc) > token_doc["expiresAt"]:
        raise HTTPException(status_code=400, detail="Ce code d'invitation a expiré")    raise HTTPException(status_code=400, detail="Ce code d'invitation a expiré")
    
    # Create userr
    new_user = {
        "username": registration.username,.username,
        "pin": registration.pin,tion.pin,
        "role": "user",
        "invitedBy": token_doc["createdBy"]   "invitedBy": token_doc["createdBy"]
    }}
    
    await users.insert_one(new_user)await users.insert_one(new_user)
    
    # Delete used token
    await invitations.delete_one({"token": registration.inviteToken})await invitations.delete_one({"token": registration.inviteToken})
    
    return {"success": True, "message": "Compte créé avec succès"}    return {"success": True, "message": "Compte créé avec succès"}


# Admin Endpoints# Admin Endpoints

@app.get("/api/admin/users")
async def get_all_users(admin_username: str):name: str):
    users = get_users_collection()users = get_users_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"}) users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")    raise HTTPException(status_code=403, detail="Accès refusé")
    
    user_list = []
    async for user in users.find({}):s.find({}):
        user_list.append({
            "id": str(user["_id"]),
            "username": user["username"],rname"],
            "role": user["role"],
            "invitedBy": user.get("invitedBy")  "invitedBy": user.get("invitedBy")
        })    })
    
    return user_list    return user_list

@app.put("/api/admin/users/{user_id}")
async def update_user(user_id: str, update: UserUpdateRequest, admin_username: str):, update: UserUpdateRequest, admin_username: str):
    users = get_users_collection()users = get_users_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"}) users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")    raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Check if new username already exists
    existing = await users.find_one({"username": update.username, "_id": {"$ne": ObjectId(user_id)}})wait users.find_one({"username": update.username, "_id": {"$ne": ObjectId(user_id)}})
    if existing:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")    raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")
    
    result = await users.update_one((
        {"_id": ObjectId(user_id)},
        {"$set": {"username": update.username}}   {"$set": {"username": update.username}}
    ))
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")    raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {"success": True}    return {"success": True}

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str, admin_username: str):, admin_username: str):
    users = get_users_collection()users = get_users_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"}) users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")    raise HTTPException(status_code=403, detail="Accès refusé")
    
    result = await users.delete_one({"_id": ObjectId(user_id)})result = await users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")    raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {"success": True}    return {"success": True}

@app.post("/api/admin/users/{user_id}/reset-pin")
async def reset_user_pin(user_id: str, admin_username: str):str, admin_username: str):
    users = get_users_collection()users = get_users_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"}) users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")    raise HTTPException(status_code=403, detail="Accès refusé")
    
    result = await users.update_one((
        {"_id": ObjectId(user_id)},},
        {"$set": {"pin": "0000"}}   {"$set": {"pin": "0000"}}
    ))
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")    raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {"success": True, "message": "Code PIN réinitialisé à 0000"}    return {"success": True, "message": "Code PIN réinitialisé à 0000"}

@app.post("/api/admin/generate-invite", response_model=InviteTokenResponse)l=InviteTokenResponse)
async def generate_invite_token(admin_username: str):min_username: str):
    users = get_users_collection()
    invitations = get_invitations_collection()invitations = get_invitations_collection()
    
    # Verify admin
    admin = await users.find_one({"username": admin_username, "role": "admin"}) users.find_one({"username": admin_username, "role": "admin"})
    if not admin:
        raise HTTPException(status_code=403, detail="Accès refusé")    raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Generate token
    token = secrets.token_urlsafe(16))
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    invitation = {
        "token": token,
        "createdBy": admin_username,name,
        "expiresAt": expires_at   "expiresAt": expires_at
    }}
    
    await invitations.insert_one(invitation)await invitations.insert_one(invitation)
    
    return InviteTokenResponse(token=token, expiresAt=expires_at)    return InviteTokenResponse(token=token, expiresAt=expires_at)


# Update slot registration endpoints# Update slot registration endpoints

@app.post("/api/register", response_model=SlotResponse)
async def register_player(registration: PlayerRegistration, username: str):tion: PlayerRegistration, username: str):
    # Verify user is authenticated
    users = get_users_collection()
    user = await users.find_one({"username": username}) users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")    raise HTTPException(status_code=403, detail="Authentification requise")
    
    collection = get_collection()
    target_date = get_next_wednesday_at_19()target_date = get_next_wednesday_at_19()
    
    slot = await collection.find_one({"date": target_date})slot = await collection.find_one({"date": target_date})
    
    if not slot:
        slot = {
            "date": target_date,_date,
            "players": [],
            "is_full": False   "guests": [],
        }
        await collection.insert_one(slot)    }
    sert_one(slot)
    if slot.get("is_full"):
        raise HTTPException(status_code=400, detail="Le créneau est complet")# Check total capacity (players + guests)
    layers", [])) + len(slot.get("guests", []))
    # Check if user already registered
    if username in slot["players"]:
        raise HTTPException(status_code=400, detail="Vous êtes déjà inscrit")    raise HTTPException(status_code=400, detail="Le créneau est complet")
    
    if len(slot["players"]) >= MAX_PLAYERS:ed
        await collection.update_one( p in slot.get("players", [])]
            {"date": target_date},
            {"$set": {"is_full": True}}aise HTTPException(status_code=400, detail="Vous êtes déjà inscrit")
        )
        raise HTTPException(status_code=400, detail="Le créneau est complet")# Register user with reference
    n.update_one(
    # Register user
    await collection.update_one({
        {"date": target_date},
        {"$push": {"players": username}}       "username": username
    )    }}}
    
    updated_slot = await collection.find_one({"date": target_date})
    ": target_date})
    if len(updated_slot["players"]) >= MAX_PLAYERS:lot.get("players", [])) + len(updated_slot.get("guests", []))
        await collection.update_one(
            {"date": target_date},
            {"$set": {"is_full": True}}wait collection.update_one(
        )
        updated_slot["is_full"] = True        {"$set": {"is_full": True}}
    
    return SlotResponse(
        date=updated_slot["date"].isoformat(),
        players=updated_slot["players"],
        player_count=len(updated_slot["players"]),"] for p in updated_slot.get("players", [])]
        max_players=MAX_PLAYERSuests_list = [f"(Invité) {g['name']} [par {g['invitedBy']}]" for g in updated_slot.get("guests", [])]
    )    

@app.post("/api/register-guest", response_model=SlotResponse)
async def register_guest(guest: GuestRegistration, username: str):sts_list,
    users = get_users_collection()
    user = await users.find_one({"username": username})ers=MAX_PLAYERS
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")
    response_model=SlotResponse)
    collection = get_collection()ation, username: str):
    target_date = get_next_wednesday_at_19()users = get_users_collection()
    
    slot = await collection.find_one({"date": target_date})if not user:
    TPException(status_code=403, detail="Authentification requise")
    if not slot:
        slot = {)
            "date": target_date,_wednesday_at_19()
            "players": [],
            "is_full": False= await collection.find_one({"date": target_date})
        }
        await collection.insert_one(slot)if not slot:
    
    if slot.get("is_full"):
        raise HTTPException(status_code=400, detail="Le créneau est complet")        "players": [],
    
    if len(slot["players"]) >= MAX_PLAYERS:
        await collection.update_one(
            {"date": target_date},t)
            {"$set": {"is_full": True}}
        )
        raise HTTPException(status_code=400, detail="Le créneau est complet")total_registered = len(slot.get("players", [])) + len(slot.get("guests", []))
    
    # Format guest name
    guest_display_name = f"(Invité) {guest.guestName} [par {username}]"    raise HTTPException(status_code=400, detail="Le créneau est complet")
    
    await collection.update_one( reference
        {"date": target_date},
        {"$push": {"players": guest_display_name}}   {"date": target_date},
    )    {"$push": {"guests": {
    
    updated_slot = await collection.find_one({"date": target_date})        "invitedBy_id": str(user["_id"]),
    
    if len(updated_slot["players"]) >= MAX_PLAYERS:
        await collection.update_one(
            {"date": target_date},
            {"$set": {"is_full": True}}ed_slot = await collection.find_one({"date": target_date})
        )t.get("players", [])) + len(updated_slot.get("guests", []))
        updated_slot["is_full"] = True
    >= MAX_PLAYERS:
    return SlotResponse(
        date=updated_slot["date"].isoformat(),
        players=updated_slot["players"],
        player_count=len(updated_slot["players"]),
        max_players=MAX_PLAYERS   updated_slot["is_full"] = True
    )    
lity
@app.delete("/api/unregister/{player_name}")players", [])]
async def unregister_player(player_name: str, username: str):name']} [par {g['invitedBy']}]" for g in updated_slot.get("guests", [])]
    users = get_users_collection()
    user = await users.find_one({"username": username})esponse(
    if not user:
        raise HTTPException(status_code=403, detail="Authentification requise")    players=players_list + guests_list,
    ered,
    collection = get_collection()
    target_date = get_next_wednesday_at_19())
    
    slot = await collection.find_one({"date": target_date}).delete("/api/unregister/{player_name}")
    ster_player(player_name: str, username: str):
    if not slot:
        raise HTTPException(status_code=404, detail="Créneau non trouvé")user = await users.find_one({"username": username})
    
    # Check permissionse=403, detail="Authentification requise")
    is_admin = user["role"] == "admin"
    is_own_registration = player_name == username
    is_own_guest = f"[par {username}]" in player_nametarget_date = get_next_wednesday_at_19()
    
    if not (is_admin or is_own_registration or is_own_guest):
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas supprimer cette inscription")
    
    if player_name not in slot["players"]:)
        raise HTTPException(status_code=404, detail="Joueur non trouvé")
    ve
    await collection.update_one( "admin"
        {"date": target_date},
        {"$pull": {"players": player_name}, "$set": {"is_full": False}} Try to remove from players
    )player_found = False
    
    updated_slot = await collection.find_one({"date": target_date})    if player["username"] == player_name:
    or player["user_id"] == str(user["_id"]):
    return SlotResponse(
        date=updated_slot["date"].isoformat(),},
        players=updated_slot["players"],me": player_name}}}
        player_count=len(updated_slot["players"]),
        max_players=MAX_PLAYERS           player_found = True
    )                break
            else:
se HTTPException(status_code=403, detail="Vous ne pouvez pas supprimer cette inscription")
@app.get("/health")
async def health_check(): if not found in players
    """Health check endpoint"""ot player_found:
    try: name from format "(Invité) Name [par username]"
        # Ping database:
        await db_client.admin.command('ping')t_name = player_name.split("(Invité) ")[1].split(" [par ")[0]
        return {t("guests", []):
            "status": "healthy",guest_name:
            "database": "connected",_id"] == str(user["_id"]):
            "timestamp": datetime.now().isoformat()               await collection.update_one(
        }  {"date": target_date},
    except Exception as e:            {"$pull": {"guests": {"name": guest_name}}}
        return {
            "status": "unhealthy",True
            "database": "disconnected",k
            "error": str(e),
            "timestamp": datetime.now().isoformat()               raise HTTPException(status_code=403, detail="Vous ne pouvez pas supprimer cette inscription")
        }    

    if not player_found:
        raise HTTPException(status_code=404, detail="Joueur non trouvé")
    
    # Always set is_full to false after removal
    await collection.update_one(
        {"date": target_date},
        {"$set": {"is_full": False}}
    )
    
    updated_slot = await collection.find_one({"date": target_date})
    total_registered = len(updated_slot.get("players", [])) + len(updated_slot.get("guests", []))
    
    # Format response for frontend compatibility
    players_list = [p["username"] for p in updated_slot.get("players", [])]
    guests_list = [f"(Invité) {g['name']} [par {g['invitedBy']}]" for g in updated_slot.get("guests", [])]
    
    return SlotResponse(
        date=updated_slot["date"].isoformat(),
        players=players_list + guests_list,
        player_count=total_registered,
        max_players=MAX_PLAYERS
    )

@app.post("/api/auth/change-pin")
async def change_pin(username: str, old_pin: str, new_pin: str):
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
