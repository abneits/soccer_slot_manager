# Soccer Slot Manager ⚽

A lightweight web application to manage reservations for indoor soccer slots. Built with FastAPI, MongoDB, and Vue.js 3.

## Features

- 🗓️ Automatic detection of next Wednesday at 19:00
- 👥 Maximum 10 players per slot
- ✅ Real-time player registration
- 🔒 Automatic slot locking when full
- 📱 Responsive design
- 🐳 Docker-ready deployment

## Tech Stack

- **Backend:** FastAPI + Uvicorn
- **Database:** MongoDB Atlas (async with Motor)
- **Frontend:** Vue.js 3 (CDN, no build tools)
- **Deployment:** Docker + Docker Compose

## Project Structure

```
soccer_slot_manager/
├── app/
│   ├── main.py           # FastAPI application & business logic
│   ├── models.py         # Pydantic data models
│   └── templates/
│       └── index.html    # Vue.js frontend
├── requirements.txt      # Python dependencies
├── Dockerfile           # Production Docker image
├── docker-compose.yml   # Docker Compose configuration
└── .env.example         # Environment variables template
```

## Quick Start

### 1. Setup Environment Variables

Copy the example environment file and configure your MongoDB URI:

```bash
cp .env.example .env
```

Edit `.env` and set your MongoDB Atlas connection string:

```
MONGO_URI=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/soccer_slots?retryWrites=true&w=majority
```

### 2. Local Development (Without Docker)

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the application at: http://localhost:8000

### 3. Production Deployment (With Docker)

Build and run with Docker Compose:

```bash
docker-compose up -d
```

The application will be available at: http://localhost:8000

View logs:

```bash
docker-compose logs -f
```

Stop the application:

```bash
docker-compose down
```

## API Endpoints

### `GET /api/current-slot`

Get or create the current slot for the next Wednesday at 19:00.

**Response:**
```json
{
  "date": "2025-12-10T19:00:00",
  "players": ["Alice", "Bob"],
  "is_full": false,
  "player_count": 2,
  "max_players": 10
}
```

### `POST /api/register`

Register a player for the current slot.

**Request:**
```json
{
  "name": "John Doe"
}
```

**Response:**
```json
{
  "date": "2025-12-10T19:00:00",
  "players": ["Alice", "Bob", "John Doe"],
  "is_full": false,
  "player_count": 3,
  "max_players": 10
}
```

**Error Cases:**
- 400: Slot is full (10 players)
- 400: Player already registered

### `GET /health`

Health check endpoint for monitoring.

## Business Logic

### Date Calculation

The system automatically calculates the "next Wednesday at 19:00":

- If today is Wednesday **before 19:00** → Returns today at 19:00
- If today is Wednesday **after 19:00** → Returns next Wednesday at 19:00
- For any other day → Returns next Wednesday at 19:00

### Slot Management

- Each slot has a maximum capacity of **10 players**
- When the 10th player registers, the slot is automatically marked as full
- The frontend auto-refreshes every 30 seconds to show updates
- Duplicate registrations are prevented

## Database Schema

**Collection:** `slots`

**Document Structure:**
```json
{
  "date": "2025-12-10T19:00:00",
  "players": ["Player 1", "Player 2", "..."],
  "is_full": false
}
```

## Development

### Running Tests

```bash
# Add your test command here when tests are implemented
pytest
```

### Code Structure

- **`app/main.py`**: FastAPI app, routes, business logic, MongoDB connection
- **`app/models.py`**: Pydantic models for validation
- **`app/templates/index.html`**: Vue.js 3 SPA (no build tools)

### Key Design Decisions

1. **No Build Tools**: Vue.js 3 is loaded via CDN for simplicity
2. **Async MongoDB**: Using Motor for non-blocking database operations
3. **Single Container**: Both API and frontend served from one container
4. **Lifespan Manager**: Proper MongoDB connection handling with FastAPI lifespan

## Configuration

### Environment Variables

- `MONGO_URI`: MongoDB connection string (required)

### Constants (in `app/main.py`)

- `MAX_PLAYERS`: 10
- `MATCH_HOUR`: 19
- `MATCH_MINUTE`: 0
- `MATCH_DAY`: 2 (Wednesday)

## Troubleshooting

### MongoDB Connection Issues

Check your connection string in `.env` or docker-compose.yml. Ensure:
- Correct username and password
- Network access is allowed from your IP
- Database user has read/write permissions

### Port Already in Use

If port 8000 is already in use, modify the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"  # Change 8080 to your preferred port
```

## License

MIT

## Author

Built for managing indoor soccer reservations.
