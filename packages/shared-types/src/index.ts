/**
 * OS Privacidad — Tipos Compartidos
 * ===================================
 * Tipos TypeScript generados desde el schema OpenAPI de la API.
 * Se generan automáticamente — no editar manualmente.
 *
 * Generación: pnpm --filter @os-privacidad/shared-types generate
 */

// ── Tipos base (se llenarán con openapi-typescript en Fase 1) ──

/** Respuesta estándar de error de la API */
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

/** Respuesta del health check */
export interface HealthResponse {
  status: "ok" | "degraded";
  db: "connected" | "disconnected" | "error";
  redis: "connected" | "disconnected" | "error";
}

/** Roles del sistema (sección 4 del Build Prompt) */
export type UserRole =
  | "super_admin"
  | "tenant_admin"
  | "dpo"
  | "analista"
  | "auditor"
  | "cliente";

/** Planes de tenant */
export type TenantPlan = "community" | "professional" | "enterprise";

/** Estados de Caso (máquina de estados 3.1) */
export type CasoEstado =
  | "abierto"
  | "en_investigacion"
  | "en_comite"
  | "cerrado"
  | "reabierto";

/** Estados de Riesgo (máquina de estados 3.2) */
export type RiesgoEstado =
  | "identificado"
  | "evaluado"
  | "en_tratamiento"
  | "mitigado"
  | "aceptado"
  | "transferido";

/** Estados de Acción (máquina de estados 3.3) */
export type AccionEstado =
  | "pendiente"
  | "en_progreso"
  | "completada"
  | "vencida";
