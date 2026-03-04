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

## Quick start (use prebuilt images)

```bash
# 1. Copy and fill the single env file
cp .env.example .env

# 2. Start everything from Docker Hub images
docker compose pull
docker compose up -d

# 3. API docs available at:
#    https://api.downloadino.com/api/docs
```

`docker-compose.yml` is configured to use:
- `voidtrek/downloadino_backend:latest`
- `voidtrek/downloadino_frontend:latest`
- `voidtrek/downloadino_nginx:latest`

So on your server, you only need:
- `docker-compose.yml`
- `.env`

No per-service `.env` files are required.

## Build and push images to Docker Hub

Run these commands from project root on your own machine:

```bash
# 1) Login
docker login

# 2) Build images
docker build -t voidtrek/downloadino_backend:latest ./backend
docker build -t voidtrek/downloadino_frontend:latest ./frontend
docker build -t voidtrek/downloadino_nginx:latest ./nginx

# 3) Push images
docker push voidtrek/downloadino_backend:latest
docker push voidtrek/downloadino_frontend:latest
docker push voidtrek/downloadino_nginx:latest
```

If you want versioned releases too, tag before push (repeat for all three images):

```bash
docker tag voidtrek/downloadino_backend:latest voidtrek/downloadino_backend:v1.0.0
docker push voidtrek/downloadino_backend:v1.0.0
```

## Default admin
Username: admin  
Password: set in `.env` → `SUPERADMIN_PASSWORD`
