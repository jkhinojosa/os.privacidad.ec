# OS Privacidad

**Sistema Operativo de Privacidad y Protección de Datos Personales**

Plataforma SaaS multitenancy para la gestión integral de privacidad, cumplimiento normativo y protección de datos personales.

---

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend API | FastAPI + Python 3.12+ |
| Frontend | Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui |
| Base de Datos | PostgreSQL 16 con RLS (Row-Level Security) |
| Cache/Sesiones | Redis 7 |
| ORM | SQLAlchemy 2.0 (async) |
| Migraciones | Alembic |
| Reverse Proxy | Nginx |
| Contenedores | Docker Compose |
| CI/CD | GitHub Actions |

## Arquitectura

- **Multitenancy**: Single database con `tenant_id` + PostgreSQL RLS
- **Auth**: JWT (access 15min) + refresh token rotativo (httpOnly cookie)
- **IA**: Interfaz abstracta `AIProvider` — independiente de proveedor
- **API**: Versionada `/api/v1/`, respuestas de error estandarizadas

## Inicio Rápido

### Prerrequisitos

- Docker + Docker Compose
- Git

### Setup

```bash
# 1. Clonar el repositorio
git clone https://github.com/jkhinojosa/os.privacidad.ec.git
cd os.privacidad.ec

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores (mínimo: POSTGRES_PASSWORD, JWT_SECRET)

# 3. Levantar servicios
docker compose up -d --build

# 4. Verificar
curl http://localhost:8000/api/v1/health
# → {"status":"ok","db":"connected","redis":"connected"}

# 5. Acceder
# API docs:  http://localhost:8000/docs
# Frontend:  http://localhost:3000
# Nginx:     http://localhost
```

### Desarrollo Local (alternativa)

```bash
# Backend (requiere uv)
cd apps/api
uv sync
uv run uvicorn main:app --reload --port 8000

# Frontend (requiere pnpm)
cd apps/web
pnpm install
pnpm dev
```

## Estructura del Proyecto

```
os-privacidad/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js frontend
├── packages/
│   └── shared-types/ # Tipos TypeScript compartidos
├── nginx/            # Configuración Nginx
├── docker-compose.yml
└── .env.example
```

## Licencia

Privado — © OS Privacidad
