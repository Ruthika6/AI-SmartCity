# Deployment Guide: Local Setup and Production Scaling

This guide outlines the steps required to set up, run, and scale the AURA platform. It includes instructions for both a zero-configuration local run (using SQLite) and a containerized production deployment (using PostgreSQL/PostGIS, Redis, and Docker).

---

## 1. Local Quickstart (Zero-Configuration Developer Mode)

The hackathon prototype is optimized for instant execution without external database setups.

### Prerequisites
* Python 3.9 or higher
* Node.js / NPM (if modifying frontend bundles; optional, as the prototype runs on standard HTML5)

### Steps
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourteam/aura-aqi-platform.git
   cd aura-aqi-platform
   ```
2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```
4. **Launch the FastAPI application:**
   ```bash
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
5. **Access the application:**
   * Open your web browser and navigate to `http://localhost:8000`.
   * Open API documentation at `http://localhost:8000/docs`.

---

## 2. Production Deployment (Dockerized PostGIS Architecture)

For production environments, AURA utilizes Docker Compose to manage the database, task workers, caching servers, and API services.

### Core Services Structure
* **App Server:** FastAPI serving JSON payloads and frontend views.
* **Database:** PostgreSQL 15 + PostGIS geospatial extensions.
* **Cache & Message Broker:** Redis for Celery tasks and session state.
* **Task Worker:** Celery executing data scraping cron-jobs every 15 minutes.

### 2.1. Environment Variables (`.env`)
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://aura_admin:secure_password@db:5432/aura_db
REDIS_URL=redis://redis:6379/0
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
LOG_LEVEL=info
```

### 2.2. Docker Compose Configuration (`docker-compose.yml`)
```yaml
version: '3.8'

services:
  db:
    image: postgis/postgis:15-3.3
    container_name: aura_postgis_db
    environment:
      POSTGRES_USER: aura_admin
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: aura_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    container_name: aura_cache_redis
    ports:
      - "6379:6379"
    restart: always

  web:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: aura_fastapi_app
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000
    volumes:
      - ./backend:/app/backend
      - ./frontend:/app/frontend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://aura_admin:secure_password@db:5432/aura_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: always

volumes:
  pgdata:
```

### 2.3. Dockerfile (`backend/Dockerfile`)
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for spatial operations (GDAL, PROJ)
RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend
COPY frontend/ ./frontend

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.4. Production Deployment Execution
1. Run `docker-compose up -d --build`.
2. Access the live platform behind an Nginx reverse proxy routing port `8000` with SSL enabled.
