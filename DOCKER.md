# 🐳 Docker Deployment Guide

This guide explains how to deploy the Soccer Slot Manager using Docker and Docker Compose.

## Prerequisites

- Docker (v20.10 or higher)
- Docker Compose (v2.0 or higher)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd soccer_slot_manager
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set a strong JWT secret:
   ```env
   JWT_SECRET=your_very_secure_random_string_here
   ```

3. **Build and start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000/api
   - MongoDB: localhost:27017

## Architecture

The Docker setup includes three services:

- **MongoDB** (Port 27017): Database service
- **Backend** (Port 5000): Python/Flask API
- **Frontend** (Port 3000): React app served by Nginx

## Docker Commands

### Start all services
```bash
docker-compose up -d
```

### Stop all services
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### Rebuild after code changes
```bash
# Rebuild all
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build backend
docker-compose up -d --build frontend
```

### Check service status
```bash
docker-compose ps
```

### Access service shell
```bash
# Backend shell
docker-compose exec backend sh

# MongoDB shell
docker-compose exec mongodb mongosh soccer_slot_manager
```

## Initial Setup

### Create the first user (Admin)

Since registration requires a sponsor, you need to create the first user directly in MongoDB:

1. **Access MongoDB shell**
   ```bash
   docker-compose exec mongodb mongosh soccer_slot_manager
   ```

2. **Generate password hash**
   
   First, run this Python command to hash a password:
   ```bash
   docker-compose exec backend python -c "import bcrypt; print(bcrypt.hashpw('your_password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))"
   ```

3. **Insert the first user**
   ```javascript
   db.user.insertOne({
     first_name: "Admin",
     last_name: "User",
     display_name: "Admin",
     email: "admin@example.com",
     password: "$2b$12$YOUR_HASHED_PASSWORD_HERE",
     registration_date: new Date(),
     is_active: true,
     created_at: new Date(),
     updated_at: new Date()
   })
   ```

4. **Exit MongoDB shell**
   ```javascript
   exit
   ```

## Data Persistence

MongoDB data is persisted in a Docker volume named `mongodb_data`. Data will survive container restarts and rebuilds.

### Backup MongoDB data
```bash
docker-compose exec mongodb mongodump --db soccer_slot_manager --out /data/backup
docker cp soccer_mongodb:/data/backup ./backup
```

### Restore MongoDB data
```bash
docker cp ./backup soccer_mongodb:/data/backup
docker-compose exec mongodb mongorestore --db soccer_slot_manager /data/backup/soccer_slot_manager
```

## Environment Variables

Edit `.env` file to configure:

| Variable | Description | Default |
|----------|-------------|---------|
| JWT_SECRET | Secret key for JWT tokens | (required) |
| MONGODB_URI | MongoDB connection string | mongodb://mongodb:27017/soccer_slot_manager |
| PORT | Backend server port | 5000 |

## Production Deployment

### Security Best Practices

1. **Change default ports** in `docker-compose.yml`
2. **Set strong JWT_SECRET** in `.env`
3. **Use environment-specific configurations**
4. **Enable MongoDB authentication**
5. **Use reverse proxy (Nginx/Traefik)** for SSL/TLS
6. **Limit exposed ports** to only necessary ones

### Example Production docker-compose.yml

```yaml
services:
  mongodb:
    # ... existing config ...
    ports: []  # Don't expose MongoDB externally
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}

  backend:
    environment:
      - MONGODB_URI=mongodb://admin:${MONGO_PASSWORD}@mongodb:27017/soccer_slot_manager?authSource=admin
      - FLASK_ENV=production
    ports: []  # Use reverse proxy instead

  frontend:
    ports: []  # Use reverse proxy instead

  # Add reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
```

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# - MongoDB not ready: Wait for health check to pass
# - Port already in use: Change PORT in .env
```

### Frontend shows connection errors
```bash
# Verify backend is running
docker-compose ps backend

# Check backend health
curl http://localhost:5000/api/health
```

### MongoDB connection issues
```bash
# Verify MongoDB is running
docker-compose ps mongodb

# Test MongoDB connection
docker-compose exec backend python -c "from mongoengine import connect; connect(host='mongodb://mongodb:27017/soccer_slot_manager'); print('✅ Connected')"
```

### Reset everything
```bash
# Stop and remove all containers, volumes
docker-compose down -v

# Rebuild from scratch
docker-compose up -d --build
```

## Development with Docker

For development, you can mount local directories as volumes:

```yaml
services:
  backend:
    volumes:
      - ./backend:/app
    environment:
      - FLASK_ENV=development
  
  frontend:
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

## Docker Image Sizes

Approximate sizes:
- Backend: ~250MB (Python slim base)
- Frontend: ~50MB (Nginx alpine with built static files)
- MongoDB: ~700MB (Official MongoDB image)

## Support

For issues related to Docker deployment, check:
1. Service logs: `docker-compose logs`
2. Container status: `docker-compose ps`
3. Network connectivity: `docker network inspect soccer_slot_manager_soccer_network`
