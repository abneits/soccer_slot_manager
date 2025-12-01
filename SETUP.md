# Setup Instructions

## Prerequisites

- Node.js (v16 or higher)
- MongoDB (v4.4 or higher)
- npm or yarn

## Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a Python virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create environment file:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` file and update the following:
   - `MONGODB_URI`: Your MongoDB connection string
   - `JWT_SECRET`: A strong random string for JWT signing
   - `PORT`: Server port (default: 5000)

6. Make sure MongoDB is running on your system

7. Start the backend server:
   ```bash
   # Development mode (with auto-reload)
   python app.py
   
   # Or with Flask CLI
   flask run --debug
   ```

The backend API will be available at `http://localhost:5000`

## Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

## Initial Setup

### Creating the First User

Since user registration requires a sponsor, you need to create the first user directly in MongoDB:

1. Connect to your MongoDB database:
   ```bash
   mongosh soccer_slot_manager
   ```

2. Create the first user (update the values as needed):
   ```javascript
   use soccer_slot_manager
   
   db.users.insertOne({
     firstName: "Admin",
     lastName: "User",
     displayName: "Admin",
     email: "admin@example.com",
     password: "$2a$10$YourHashedPasswordHere", // You'll need to hash this
     registrationDate: new Date(),
     isActive: true
   })
   ```

3. To hash a password for the initial user, you can run this Python script:
   ```python
   import bcrypt
   password = 'your_password_here'
   hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
   print(hashed.decode('utf-8'))
   ```

4. Or you can temporarily modify the registration endpoint to allow registration without a sponsor for the first user.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user (requires sponsor)
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Users
- `GET /api/users` - Get all users
- `GET /api/users/:id` - Get user by ID
- `PUT /api/users/:id` - Update user profile

### Slots
- `GET /api/slots` - Get all slots (paginated)
- `GET /api/slots/next` - Get next Wednesday slot
- `GET /api/slots/:id` - Get slot by ID
- `POST /api/slots/:id/register` - Register for slot
- `PUT /api/slots/:id/register` - Update registration
- `DELETE /api/slots/:id/register` - Cancel registration
- `PUT /api/slots/:id/details` - Update slot details (teams/score)

### Statistics
- `GET /api/stats` - Get all statistics
- `GET /api/stats/user/:userId` - Get user-specific statistics

## Project Structure

```
soccer_slot_manager/
├── backend/
│   ├── models/          # MongoEngine models
│   ├── routes/          # Flask blueprints
│   ├── middleware/      # Flask middleware
│   ├── app.py           # Entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── context/     # React context
│   │   ├── services/    # API service
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## Features

- ✅ User authentication with JWT
- ✅ Sponsored registration system
- ✅ Weekly slot management
- ✅ Guest registration
- ✅ Match results tracking
- ✅ Player statistics
- ✅ Responsive design

## Development Tips

- Backend runs on port 5000 by default (Python/Flask)
- Frontend runs on port 3000 by default (React/Vite)
- Frontend proxies API requests to backend
- Use `python app.py` or `flask run --debug` for hot-reload during development
- Use `npm run dev` in frontend for React hot-reload
- MongoDB must be running before starting the backend
- Activate Python virtual environment before starting backend

## Troubleshooting

### MongoDB Connection Issues
- Ensure MongoDB is running: `sudo systemctl status mongod`
- Check the connection string in `.env`

### Port Already in Use
- Change the PORT in backend `.env` file
- Update the proxy target in `frontend/vite.config.js`

### Registration Issues
- Make sure you have at least one user to act as sponsor
- Check that the sponsor ID is valid

## License

MIT
