"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, setAccessToken } from "@/lib/api";

interface AuthResponse {
  token: {
    access_token: string;
    token_type: string;
    expires_in: number;
  };
  user: {
    id: string;
    email: string;
    nombre: string;
    apellido: string;
    rol: string;
    tenant_id: string | null;
  };
}

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@privacidad.ec");
  const [password, setPassword] = useState("Admin1234!");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await apiFetch<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      setAccessToken(data.token.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
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
        padding: "1.5rem",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "440px",
          background: "rgba(30, 41, 59, 0.85)",
          border: "1px solid rgba(148, 163, 184, 0.15)",
          borderRadius: "20px",
          padding: "2.5rem 2rem",
          backdropFilter: "blur(16px)",
          boxShadow: "0 16px 40px rgba(0, 0, 0, 0.4)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div
            style={{
              width: "64px",
              height: "64px",
              borderRadius: "16px",
              background: "linear-gradient(135deg, #3b82f6, #8b5cf6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 1rem",
              fontSize: "1.75rem",
              boxShadow: "0 8px 24px rgba(59, 130, 246, 0.3)",
            }}
          >
            🛡️
          </div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 700, margin: 0 }}>
            Iniciar Sesión
          </h1>
          <p style={{ fontSize: "0.9rem", color: "#94a3b8", marginTop: "0.35rem" }}>
            OS Privacidad · Acceso al Sistema
          </p>
        </div>

        {error && (
          <div
            style={{
              background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              color: "#f87171",
              padding: "0.75rem 1rem",
              borderRadius: "10px",
              fontSize: "0.85rem",
              marginBottom: "1.5rem",
            }}
          >
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "1.25rem" }}>
            <label
              style={{
                display: "block",
                fontSize: "0.85rem",
                color: "#cbd5e1",
                marginBottom: "0.5rem",
                fontWeight: 500,
              }}
            >
              Correo Electrónico
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="nombre@organizacion.ec"
              style={{
                width: "100%",
                padding: "0.75rem 1rem",
                borderRadius: "10px",
                border: "1px solid rgba(148, 163, 184, 0.2)",
                background: "rgba(15, 23, 42, 0.6)",
                color: "#fff",
                fontSize: "0.95rem",
                outline: "none",
                boxSizing: "border-box",
              }}
            />
          </div>

          <div style={{ marginBottom: "1.5rem" }}>
            <label
              style={{
                display: "block",
                fontSize: "0.85rem",
                color: "#cbd5e1",
                marginBottom: "0.5rem",
                fontWeight: 500,
              }}
            >
              Contraseña
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: "100%",
                padding: "0.75rem 1rem",
                borderRadius: "10px",
                border: "1px solid rgba(148, 163, 184, 0.2)",
                background: "rgba(15, 23, 42, 0.6)",
                color: "#fff",
                fontSize: "0.95rem",
                outline: "none",
                boxSizing: "border-box",
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "0.85rem",
              borderRadius: "10px",
              border: "none",
              background: "linear-gradient(135deg, #3b82f6, #6366f1)",
              color: "#fff",
              fontWeight: 600,
              fontSize: "0.95rem",
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: "0 4px 16px rgba(59, 130, 246, 0.4)",
              transition: "transform 0.1s ease",
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? "Ingresando..." : "Ingresar"}
          </button>
        </form>

        {/* Cuentas Demo Rápidas */}
        <div style={{ marginTop: "2rem", borderTop: "1px solid rgba(148, 163, 184, 0.1)", paddingTop: "1.5rem" }}>
          <p style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
            Credenciales de Prueba (Demo)
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <button
              type="button"
              onClick={() => handleQuickLogin("admin@privacidad.ec", "Admin1234!")}
              style={{
                background: "rgba(16, 185, 129, 0.1)",
                border: "1px solid rgba(16, 185, 129, 0.2)",
                color: "#6ee7b7",
                padding: "0.5rem 0.75rem",
                borderRadius: "8px",
                fontSize: "0.8rem",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              👑 <strong>SuperAdmin / DPD:</strong> admin@privacidad.ec
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("admin@farmandina.ec", "Admin1234!")}
              style={{
                background: "rgba(59, 130, 246, 0.1)",
                border: "1px solid rgba(59, 130, 246, 0.2)",
                color: "#93c5fd",
                padding: "0.5rem 0.75rem",
                borderRadius: "8px",
                fontSize: "0.8rem",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              🏢 <strong>Tenant FarmAndina:</strong> admin@farmandina.ec
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("dpo@demo.ec", "Admin1234!")}
              style={{
                background: "rgba(168, 85, 247, 0.1)",
                border: "1px solid rgba(168, 85, 247, 0.2)",
                color: "#d8b4fe",
                padding: "0.5rem 0.75rem",
                borderRadius: "8px",
                fontSize: "0.8rem",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              ⚖️ <strong>Oficial DPO:</strong> dpo@demo.ec
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
