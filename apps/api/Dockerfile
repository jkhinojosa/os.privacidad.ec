# ===========================================================
# OS Privacidad — API Dockerfile (Multi-stage)
# ===========================================================
# Stage 1: Development (hot-reload con uvicorn)
# Stage 2: Production (optimizado, sin dev deps)
# ===========================================================

# ── Stage 1: Development ─────────────────────────────────────
FROM python:3.12-slim AS development

# Instalar uv para gestión rápida de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copiar archivos de proyecto
COPY pyproject.toml ./

# Instalar todas las dependencias (incluye dev)
RUN uv sync --no-install-project

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Copiar código fuente
COPY . .

EXPOSE 8000

# Uvicorn con hot-reload para desarrollo
CMD uvicorn main:app --host 0.0.0.0 --port 8000 --reload


# ── Stage 2: Production ──────────────────────────────────────
FROM python:3.12-slim AS production

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Crear usuario no-root por seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copiar archivos de proyecto e instalar solo prod deps
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Copiar código fuente
COPY . .

# Cambiar a usuario no-root
USER appuser

EXPOSE 8000

# Uvicorn con workers para producción
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
