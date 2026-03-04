# Downloadino

Self-hosted GitHub-style file repository platform.

## Structure
```
downloadino/
├── backend/     FastAPI — api.downloadino.com
├── frontend/    Nuxt 3 — downloadino.com
├── nginx/       Reverse proxy
└── docker-compose.yml
```

## Quick start

```bash
# 1. Copy and fill env files
cp .env.example .env
cp backend/.env.example backend/.env   # fill S3 keys, change passwords

# 2. Start everything
docker compose up --build -d

# 3. API docs available at:
#    https://api.downloadino.com/api/docs
```

## Default admin
Username: admin  
Password: set in backend/.env → SUPERADMIN_PASSWORD
