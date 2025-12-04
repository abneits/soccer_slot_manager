# Soccer Slot Manager - AI Coding Agent Instructions

## Project Overview

This is a lightweight FastAPI application for managing indoor soccer slot reservations. The system automatically calculates the next Wednesday at 19:00, allows up to 10 players to register, and uses MongoDB Atlas for persistence.

**Key Architecture:** Single-container deployment serving both API (FastAPI) and frontend (Vue.js 3 via CDN) without build tools.

## Critical Business Logic

### Date Calculation (`get_next_wednesday_at_19()` in `app/main.py`)

The core business rule determines the target date for reservations:
- If today is Wednesday AND current time < 19:00 → use today at 19:00
- Otherwise → calculate next Wednesday at 19:00
- This logic is CRITICAL and should not be changed without explicit discussion

### Slot Management Rules

1. **Maximum capacity:** Exactly 10 players per slot
2. **Full slot detection:** When `len(players) >= MAX_PLAYERS`, set `is_full = True`
3. **Duplicate prevention:** Check if player name already exists before registration
4. **Automatic slot creation:** `GET /api/current-slot` creates slot if it doesn't exist

## Technology Constraints

### Frontend: Vue.js 3 Without Build Tools

- **NEVER suggest:** Webpack, Vite, npm build scripts, or .vue single-file components
- **Always use:** Vue.js 3 loaded via CDN (`<script src="https://unpkg.com/vue@3/dist/vue.global.js">`)
- **Pattern:** All Vue logic lives in `<script>` tags in `app/templates/index.html`
- **Reason:** Deployment simplicity for NAS hosting

### Database: Async MongoDB with Motor

- **NEVER use:** `pymongo` (synchronous driver)
- **Always use:** `motor` for async operations with `AsyncIOMotorClient`
- **Connection pattern:** Managed via FastAPI lifespan context manager (see `lifespan()` in `app/main.py`)
- **Collection access:** Use helper functions `get_db()` and `get_collection()`

### API Design Patterns

- **Validation:** Pydantic models in `app/models.py` handle all input/output validation
- **Error handling:** Return `HTTPException` with 400 status for business logic violations
- **Response models:** Use `SlotResponse` for consistent API responses

## Development Workflows

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONGO_URI="mongodb+srv://..."

# Run with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f soccer-app

# Rebuild after code changes
docker-compose up -d --build
```

### Testing Database Connection

Use the `/health` endpoint to verify MongoDB connectivity without modifying data.

## Code Conventions

### File Organization

- **`app/main.py`**: All routes, business logic, and MongoDB connection management
- **`app/models.py`**: Pydantic models only (no business logic)
- **`app/templates/index.html`**: Complete Vue.js SPA with inline styles

### Naming Patterns

- **API routes:** Use snake_case for function names (`get_current_slot`, `register_player`)
- **Pydantic models:** Use PascalCase (`Slot`, `PlayerRegistration`, `SlotResponse`)
- **Frontend:** Use camelCase for Vue.js methods and data properties

### Constants Configuration

All configurable values are constants in `app/main.py`:
- `MAX_PLAYERS = 10`
- `MATCH_HOUR = 19`
- `MATCH_MINUTE = 0`
- `MATCH_DAY = 2` (Wednesday, where 0=Monday)

**When suggesting changes:** Always modify constants, never hardcode values.

## Common Modification Patterns

### Adding a New API Endpoint

1. Define Pydantic request/response models in `app/models.py`
2. Add async route handler in `app/main.py`
3. Use `get_collection()` for database access
4. Return appropriate response model or raise `HTTPException`

### Modifying Frontend Behavior

- **State management:** Add reactive properties to Vue's `data()` function
- **API calls:** Use `fetch()` with async/await in Vue methods
- **Styling:** Add inline CSS in the `<style>` block (no external CSS files)

### Changing Slot Capacity

Modify `MAX_PLAYERS` constant in `app/main.py`. Frontend table automatically adjusts via `v-for="index in 10"`.

## Integration Points

### MongoDB Atlas Connection

- **Environment variable:** `MONGO_URI` (passed via `.env` or docker-compose)
- **Connection lifecycle:** Managed in `lifespan()` context manager
- **Database name:** `soccer_slots` (hardcoded in `DB_NAME`)
- **Collection name:** `slots` (hardcoded in `COLLECTION_NAME`)

### Frontend-Backend Communication

- **Endpoint discovery:** Frontend uses relative URLs (`/api/current-slot`, `/api/register`)
- **Auto-refresh:** Vue component fetches data every 30 seconds via `setInterval()`
- **Error display:** Backend error messages shown in frontend via `response.json().detail`

## Debugging Tips

### MongoDB Connection Issues

Check `docker-compose logs -f` for connection errors. The lifespan manager logs connection status on startup.

### Date Calculation Verification

Add temporary logging in `get_next_wednesday_at_19()` to verify date logic:
```python
target_date = get_next_wednesday_at_19()
print(f"Calculated target date: {target_date}")
```

### Frontend State Issues

Open browser DevTools console to see Vue component state and API responses.

## DO NOT Suggest

- ❌ Adding a build step or bundler (Webpack, Vite, Parcel)
- ❌ Using synchronous database operations
- ❌ Splitting Vue component into separate .vue files
- ❌ Adding authentication (not in current scope)
- ❌ Changing the Wednesday 19:00 logic without explicit requirement

## When Making Changes

1. **Preserve async patterns:** All database operations must use `await`
2. **Maintain Vue CDN approach:** No build tools should be introduced
3. **Respect the 10-player limit:** This is a hard business constraint
4. **Keep single-container deployment:** Don't suggest separate frontend/backend containers
5. **Test date logic carefully:** The Wednesday calculation is business-critical

## Additional Context

- **Target deployment:** Synology NAS or similar lightweight hosting
- **User base:** Small group (< 50 users), no high-traffic concerns
- **Language preference:** French for frontend UI text
- **No authentication:** Trust-based system, players self-register by name
