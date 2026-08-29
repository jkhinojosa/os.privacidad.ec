-- ===========================================================
-- OS Privacidad — PostgreSQL Init Script
-- ===========================================================
-- Se ejecuta automáticamente al crear el contenedor de BD.
-- Crea el rol app_user (no superuser) para RLS compliance.
-- ===========================================================

-- Crear rol de aplicación (no superuser, no bypass RLS)
-- Este rol es el que la aplicación usa para conectarse.
-- Los superusers y table owners bypass RLS automáticamente,
-- así que usamos un rol dedicado.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user WITH LOGIN PASSWORD 'changeme';
    END IF;
END
$$;

-- Otorgar permisos al esquema público
GRANT USAGE ON SCHEMA public TO app_user;
GRANT CREATE ON SCHEMA public TO app_user;

-- Permisos por defecto para tablas futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;

-- Permisos por defecto para secuencias futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO app_user;

-- Habilitar extensión uuid-ossp (para gen_random_uuid en versiones < 13)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Nota: gen_random_uuid() está disponible nativamente desde PostgreSQL 13+
-- pero la extensión es un fallback seguro.
