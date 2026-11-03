

# Mirrorino

> Un espejo de GitHub autoalojado diseñado para mantener el software de código abierto accesible cuando Internet se desconecta.

🚀 Sirvió más de **6,000,000 solicitudes** durante la interrupción de Internet en Irán en 2026.

<p align="center">
  <img width="1125" height="630" alt="Screenshot (133)" src="https://github.com/user-attachments/assets/e31a70ec-f493-44da-9aa3-2438f6ea7b5c" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688">
  <img src="https://img.shields.io/badge/Nuxt-Frontend-00DC82">
  <img src="https://img.shields.io/badge/PostgreSQL-Database-336791">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED">
  <img src="https://img.shields.io/badge/License-MIT-blue">
</p>

## ¿Por qué Mirrorino?

Cuando el acceso a GitHub se volvió poco fiable durante el apagón nacional de Internet en Irán,
los desarrolladores aún necesitaban paquetes, repositorios y documentación.

Mirrorino se creó para resolver exactamente ese problema.

En lugar de depender de la disponibilidad de GitHub, las organizaciones pueden implementar su propio espejo en minutos.

Durante el apagón, Mirrorino sirvió más de

# 6,000,000 solicitudes

haciendo que los repositorios de código abierto estuvieran disponibles incluso cuando GitHub era inaccesible.

## Véalo en acción

<img width="1280" height="720" alt="Timeline 1 (1)" src="https://github.com/user-attachments/assets/683fe03f-ee4b-449a-a940-a2fc7b606e02" />

## ✨ Características

- 📦 Plataforma de repositorios similar a GitHub autoalojada
- 🔍 Búsqueda rápida de repositorios
- 📂 Navegador de archivos con navegación por directorios
- 📄 Vista previa de Markdown y código
- 👤 Autenticación y gestión de usuarios
- ⚡ API REST con FastAPI
- 🐳 Despliegue en Docker con un solo comando
- 🌐 Interfaz de usuario moderna y receptiva
- 🔒 Proxy inverso con Nginx

## Capturas de pantalla

### Vista del repositorio

<img width="100%" alt="Screenshot (208)" src="https://github.com/user-attachments/assets/fa584e6b-3a8c-4373-a8f6-9e3055cb366c" />

### Panel de administración

<img width="100%" alt="Screenshot (197)" src="https://github.com/user-attachments/assets/0a349f84-893b-4dec-b729-67ce60e34768" />

### Gestión de usuarios

<img width="100%" alt="Screenshot (199)" src="https://github.com/user-attachments/assets/e4ec6d4e-421a-48f3-9353-d8f269ba910b" />

### Estadísticas

<img width="100%" alt="Screenshot (198)" src="https://github.com/user-attachments/assets/44c9bd3e-8bc3-43bb-9cf2-7689e5dec0e2" />

## Estructura
```
mirrorino/
├── backend/     FastAPI — api.mirrorino.com
├── frontend/    Nuxt 3 — mirrorino.com
├── nginx/       Reverse proxy
└── docker-compose.yml
```

## Inicio rápido

```bash
# 1. Copia y completa el único archivo de entorno
cp .env.example .env

# 2. Inicia todo desde las imágenes de Docker Hub
git clone https://github.com/AmirHBuilds/mirrorino
docker compose up -d

# 3. Documentación de la API disponible en:
#    https://api.mirrorino.com/api/docs
```

### Modo de iconos sin conexión (no se necesita Internet público)

Este proyecto está configurado para cargar iconos desde archivos locales en `frontend/icons/mdi` mediante colecciones personalizadas de Nuxt Icon.
No se requiere acceso a la API de Iconify.


## Administrador predeterminado
Usuario: admin  
Contraseña: definida en `.env` → `SUPERADMIN_PASSWORD`
