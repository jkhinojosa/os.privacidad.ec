"use client";

import { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
  db: string;
  redis: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
        const res = await fetch(`${apiUrl}/health`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setHealth(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error de conexión");
      } finally {
        setLoading(false);
      }
    };
    checkHealth();
  }, []);

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
        padding: "2rem",
      }}
    >
      {/* Logo / Brand */}
      <div style={{ textAlign: "center", marginBottom: "3rem" }}>
        <div
          style={{
            width: "80px",
            height: "80px",
            borderRadius: "20px",
            background: "linear-gradient(135deg, #3b82f6, #8b5cf6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 1.5rem",
            fontSize: "2rem",
            boxShadow: "0 8px 32px rgba(59, 130, 246, 0.3)",
          }}
        >
          🛡️
        </div>
        <h1
          style={{
            fontSize: "2.5rem",
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
            fontSize: "1.1rem",
            color: "#94a3b8",
            marginTop: "0.5rem",
            maxWidth: "500px",
          }}
        >
          Sistema Operativo de Privacidad y Protección de Datos Personales
        </p>
      </div>

      {/* Health Status Card */}
      <div
        style={{
          background: "rgba(30, 41, 59, 0.8)",
          border: "1px solid rgba(148, 163, 184, 0.1)",
          borderRadius: "16px",
          padding: "2rem",
          width: "100%",
          maxWidth: "420px",
          backdropFilter: "blur(12px)",
          boxShadow: "0 4px 24px rgba(0, 0, 0, 0.3)",
        }}
      >
        <h2
          style={{
            fontSize: "0.85rem",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "#64748b",
            margin: "0 0 1.5rem 0",
          }}
        >
          Estado del Sistema
        </h2>

        {loading ? (
          <div style={{ textAlign: "center", padding: "1rem", color: "#64748b" }}>
            <div
              style={{
                width: "24px",
                height: "24px",
                border: "3px solid rgba(59, 130, 246, 0.2)",
                borderTop: "3px solid #3b82f6",
                borderRadius: "50%",
                animation: "spin 1s linear infinite",
                margin: "0 auto 0.75rem",
              }}
            />
            Verificando servicios...
          </div>
        ) : error ? (
          <StatusRow label="API" status="error" detail={error} />
        ) : health ? (
          <>
            <StatusRow
              label="API"
              status={health.status === "ok" ? "ok" : "warning"}
              detail={health.status === "ok" ? "Operativo" : "Degradado"}
            />
            <StatusRow
              label="PostgreSQL"
              status={health.db === "connected" ? "ok" : "error"}
              detail={health.db === "connected" ? "Conectado" : health.db}
            />
            <StatusRow
              label="Redis"
              status={health.redis === "connected" ? "ok" : "error"}
              detail={health.redis === "connected" ? "Conectado" : health.redis}
            />
          </>
        ) : null}
      </div>

      {/* Version badge */}
      <p
        style={{
          marginTop: "2rem",
          fontSize: "0.8rem",
          color: "#475569",
        }}
      >
        v0.1.0 — Fase 0 Setup
      </p>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
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
