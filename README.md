# Mirrorino

Self-hosted GitHub-style file repository platform.

## Structure
```
mirrorino/
├── backend/     FastAPI — api.mirrorino.com
├── frontend/    Nuxt 3 — mirrorino.com
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
#    https://api.mirrorino.com/api/docs
```

`docker-compose.yml` is configured to use:
- `voidtrek/mirrorino_backend:latest`
- `voidtrek/mirrorino_frontend:latest`
- `voidtrek/mirrorino_nginx:latest`

So on your server, you only need:
- `docker-compose.yml`
- `.env`

No per-service `.env` files are required.

### Contact details configuration

Set these values in your root `.env` file to populate `/contact` page details:

```env
NUXT_PUBLIC_SUPPORT_EMAIL=support@mirrorino.com
NUXT_PUBLIC_SUPPORT_TELEGRAM_ID=@mirrorino_support
NUXT_PUBLIC_SUPPORT_WEBSITE=https://mirrorino.com
```

Then recreate the frontend container so Nuxt picks up new env values:

```bash
docker compose up -d --build frontend
```

### Offline icon mode (no public internet needed)

This project is configured to load icons from local files under `frontend/icons/mdi` via Nuxt Icon custom collections.
No Iconify API access is required.

## Build and push images to Docker Hub

Run these commands from project root on your own machine:

```bash
# 1) Login
docker login

# 2) Build images
docker build -t voidtrek/mirrorino_backend:latest ./backend
docker build -t voidtrek/mirrorino_frontend:latest ./frontend
docker build -t voidtrek/mirrorino_nginx:latest ./nginx

# 3) Push images
docker push voidtrek/mirrorino_backend:latest
docker push voidtrek/mirrorino_frontend:latest
docker push voidtrek/mirrorino_nginx:latest
```

If you want versioned releases too, tag before push (repeat for all three images):

```bash
docker tag voidtrek/mirrorino_backend:latest voidtrek/mirrorino_backend:v1.0.0
docker push voidtrek/mirrorino_backend:v1.0.0
```

## Default admin
Username: admin  
Password: set in `.env` → `SUPERADMIN_PASSWORD`
