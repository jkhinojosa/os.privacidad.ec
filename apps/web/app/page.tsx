"use client";

import { useEffect, useState } from "react";
import Link from "next/navigation";
import { apiFetch, getAccessToken, setAccessToken } from "@/lib/api";

interface HealthStatus {
  status: string;
  db: string;
  redis: string;
}

interface UserProfile {
  id: string;
  email: string;
  nombre: string;
  apellido: string;
  rol: string;
  tenant_id: string | null;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      try {
        const healthData = await apiFetch<HealthStatus>("/health");
        setHealth(healthData);

        const token = getAccessToken();
        if (token) {
          try {
            const userData = await apiFetch<UserProfile>("/auth/me");
            setUser(userData);
          } catch {
            setAccessToken(null);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error de conexión");
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const handleLogout = async () => {
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } catch {
      // Ignorar error al cerrar sesión
    }
    setAccessToken(null);
    setUser(null);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)",
        color: "#e2e8f0",
        padding: "2rem 1rem",
      }}
    >
      {/* Header / Brand */}
      <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
        <div
          style={{
            width: "72px",
            height: "72px",
            borderRadius: "18px",
            background: "linear-gradient(135deg, #3b82f6, #8b5cf6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 1.25rem",
            fontSize: "2rem",
            boxShadow: "0 8px 32px rgba(59, 130, 246, 0.3)",
          }}
        >
          🛡️
        </div>
        <h1
          style={{
            fontSize: "2.25rem",
            fontWeight: 800,
            margin: 0,
            background: "linear-gradient(135deg, #60a5fa, #a78bfa)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            letterSpacing: "-0.02em",
          }}
        >
          OS Privacidad
        </h1>
        <p
          style={{
            fontSize: "1rem",
            color: "#94a3b8",
            marginTop: "0.5rem",
            maxWidth: "500px",
          }}
        >
          Sistema Operativo de Privacidad y Protección de Datos Personales
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", width: "100%", maxWidth: "440px" }}>
        {/* User Session Card */}
        <div
          style={{
            background: "rgba(30, 41, 59, 0.8)",
            border: "1px solid rgba(148, 163, 184, 0.15)",
            borderRadius: "16px",
            padding: "1.75rem",
            backdropFilter: "blur(12px)",
            boxShadow: "0 8px 30px rgba(0, 0, 0, 0.3)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: "#64748b",
                margin: 0,
              }}
            >
              Sesión de Usuario (Fase 1)
            </h2>
            {user && (
              <span
                style={{
                  background: "rgba(59, 130, 246, 0.2)",
                  color: "#93c5fd",
                  padding: "0.2rem 0.6rem",
                  borderRadius: "6px",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  textTransform: "uppercase",
                }}
              >
                {user.rol.replace("_", " ")}
              </span>
            )}
          </div>

          {user ? (
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
                <div
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "50%",
                    background: "linear-gradient(135deg, #6366f1, #a855f7)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: "1rem",
                  }}
                >
                  {user.nombre[0]}
                </div>
                <div>
                  <p style={{ margin: 0, fontWeight: 600, fontSize: "0.95rem" }}>
                    {user.nombre} {user.apellido}
                  </p>
                  <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.8rem" }}>
                    {user.email}
                  </p>
                </div>
              </div>

              <button
                onClick={handleLogout}
                style={{
                  width: "100%",
                  padding: "0.6rem",
                  borderRadius: "8px",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  background: "rgba(239, 68, 68, 0.15)",
                  color: "#f87171",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Cerrar Sesión
              </button>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "0.5rem 0" }}>
              <p style={{ fontSize: "0.9rem", color: "#94a3b8", marginBottom: "1rem" }}>
                No hay sesión activa. Ingresa con tus credenciales de prueba.
              </p>
              <a
                href="/login"
                style={{
                  display: "block",
                  width: "100%",
                  padding: "0.75rem",
                  borderRadius: "10px",
                  background: "linear-gradient(135deg, #3b82f6, #6366f1)",
                  color: "#fff",
                  fontWeight: 600,
                  fontSize: "0.9rem",
                  textAlign: "center",
                  textDecoration: "none",
                  boxShadow: "0 4px 16px rgba(59, 130, 246, 0.3)",
                  boxSizing: "border-box",
                }}
              >
                Ir a Iniciar Sesión →
              </a>
            </div>
          )}
        </div>

        {/* Health Status Card */}
        <div
          style={{
            background: "rgba(30, 41, 59, 0.8)",
            border: "1px solid rgba(148, 163, 184, 0.15)",
            borderRadius: "16px",
            padding: "1.75rem",
            backdropFilter: "blur(12px)",
            boxShadow: "0 8px 30px rgba(0, 0, 0, 0.3)",
          }}
        >
          <h2
            style={{
              fontSize: "0.85rem",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: "#64748b",
              margin: "0 0 1.25rem 0",
            }}
          >
            Estado del Sistema
          </h2>

          {loading ? (
            <div style={{ textAlign: "center", padding: "1rem", color: "#64748b" }}>
              Verificando servicios...
            </div>
          ) : error ? (
            <StatusRow label="API" status="error" detail={error} />
          ) : health ? (
            <>
              <StatusRow
                label="API Backend"
                status={health.status === "ok" ? "ok" : "warning"}
                detail={health.status === "ok" ? "Operativo (FastAPI)" : "Degradado"}
              />
              <StatusRow
                label="PostgreSQL (RLS)"
                status={health.db === "connected" ? "ok" : "error"}
                detail={health.db === "connected" ? "Conectado" : health.db}
              />
              <StatusRow
                label="Redis (Sesiones)"
                status={health.redis === "connected" ? "ok" : "error"}
                detail={health.redis === "connected" ? "Conectado" : health.redis}
              />
            </>
          ) : null}
        </div>
      </div>

      {/* Version badge */}
      <p
        style={{
          marginTop: "2rem",
          fontSize: "0.8rem",
          color: "#475569",
        }}
      >
        v0.2.0 — Fase 1 (Auth, RBAC & RLS Multitenancy)
      </p>
    </div>
  );
}

function StatusRow({
  label,
  status,
  detail,
}: {
  label: string;
  status: "ok" | "warning" | "error";
  detail: string;
}) {
  const colors = {
    ok: { bg: "rgba(34, 197, 94, 0.1)", dot: "#22c55e", text: "#4ade80" },
    warning: { bg: "rgba(250, 204, 21, 0.1)", dot: "#facc15", text: "#fde047" },
    error: { bg: "rgba(239, 68, 68, 0.1)", dot: "#ef4444", text: "#f87171" },
  };
  const c = colors[status];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0.75rem 1rem",
        borderRadius: "10px",
        background: c.bg,
        marginBottom: "0.5rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <div
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: c.dot,
            boxShadow: `0 0 8px ${c.dot}`,
          }}
        />
        <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>{label}</span>
      </div>
      <span style={{ fontSize: "0.85rem", color: c.text }}>{detail}</span>
    </div>
  );
}
