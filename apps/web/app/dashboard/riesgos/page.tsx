"use client";

import React, { useState, useEffect } from "react";
import {
  AlertTriangle,
  ShieldCheck,
  FileCheck,
  Plus,
  Scale,
  Activity,
  Layers,
  ArrowRight,
  TrendingDown,
  Lock,
} from "lucide-react";
import { NormativeTooltip } from "@/components/NormativeTooltip";
import { apiFetch } from "@/lib/api";

export default function RiesgosPage() {
  const [riesgos, setRiesgos] = useState<any[]>([]);
  const [matriz, setMatriz] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCelda, setSelectedCelda] = useState<{ p: number; i: number } | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [resRiesgos, resMatriz] = await Promise.allSettled([
          apiFetch<any[]>("/riesgos"),
          apiFetch<any>("/riesgos/matriz"),
        ]);
        if (resRiesgos.status === "fulfilled") setRiesgos(resRiesgos.value);
        if (resMatriz.status === "fulfilled") setMatriz(resMatriz.value);
      } catch (err) {
        console.error("Error loading riesgos:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* ── Header ────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-100">
              Gestión de Riesgos & EIPD (PIA)
            </h1>
            <NormativeTooltip
              articulo="Res. SPDP-SPD-2026-0005-R & Art. 32 RGLOPDP"
              titulo="Evaluación de Impacto en la Protección de Datos (EIPD)"
              explicacion="Metodología obligatoria de cuantificación de riesgo R = P × (I × V). Tratamientos a gran escala, datos de salud o biometría gatillan EIPD obligatoria."
              justificacionLegal="La falta de EIPD previa al inicio de tratamientos de alto riesgo está tipificada como infracción muy grave (Art. 68 LOPDP)."
              criterioTecnico="Ponderación cuantitativa con mitigación en 5 categorías: técnica, organizativa, jurídica, física e informativa."
              sancionRiesgo="Multa muy grave hasta 1% del volumen de negocio."
            />
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Matriz de calor 5 × 5, catálogo de controles multidimensionales y ciclo de vida de Evaluaciones de Impacto.
          </p>
        </div>

        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-amber-950/50">
          <Plus className="w-4 h-4" />
          <span>Evaluar Nuevo Riesgo</span>
        </button>
      </div>

      {/* ── Top Grid: 5x5 Heatmap & Formula Explanation ──────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 5x5 Interactive Heatmap (7 Cols) */}
        <div className="lg:col-span-7 p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-bold text-slate-100">
                Matriz de Calor Interactiva (Probabilidad × Impacto)
              </h3>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Vulnerabilidad Base: <strong>V = 0.5</strong>
            </span>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 space-y-3">
            <div className="grid grid-cols-5 gap-2 text-center text-xs font-mono">
              {[5, 4, 3, 2, 1].map((prob) =>
                [1, 2, 3, 4, 5].map((imp) => {
                  const score = prob * imp * 0.5;
                  const isSelected = selectedCelda?.p === prob && selectedCelda?.i === imp;

                  let bgColor = "bg-emerald-950/40 text-emerald-300 border-emerald-900/40 hover:border-emerald-500";
                  let nivelBadge = "Bajo";
                  if (score >= 8 && score < 12) {
                    bgColor = "bg-amber-950/40 text-amber-300 border-amber-900/40 hover:border-amber-500";
                    nivelBadge = "Medio";
                  } else if (score >= 12) {
                    bgColor = "bg-rose-950/40 text-rose-300 border-rose-900/40 hover:border-rose-500";
                    nivelBadge = "Crítico";
                  }

                  return (
                    <button
                      key={`${prob}-${imp}`}
                      onClick={() => setSelectedCelda({ p: prob, i: imp })}
                      className={`h-14 rounded-xl border flex flex-col items-center justify-center p-1 transition-all ${bgColor} ${
                        isSelected ? "ring-2 ring-emerald-400 scale-105" : ""
                      }`}
                    >
                      <span className="font-bold text-sm">{score.toFixed(1)}</span>
                      <span className="text-[9px] uppercase tracking-tighter opacity-80">{nivelBadge}</span>
                    </button>
                  );
                })
              )}
            </div>

            <div className="flex justify-between items-center text-[11px] text-slate-400 pt-2 border-t border-slate-800/80 font-mono">
              <span>Eje Horizontal: <strong>Impacto (1: Mínimo a 5: Catastrófico)</strong></span>
              <span>Eje Vertical: <strong>Probabilidad (1: Improbable a 5: Frecuente)</strong></span>
            </div>
          </div>
        </div>

        {/* Formula & MTGE Guidelines (5 Cols) */}
        <div className="lg:col-span-5 p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-lg space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-amber-400 font-bold text-sm mb-2">
              <Scale className="w-4 h-4" />
              <span>Metodología Cuantitativa de Riesgo LOPDP</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-200 mb-3">
              <code>Score = Probabilidad × (Impacto × Vulnerabilidad)</code>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed mb-3">
              Bajo la <strong>Resolución SPDP-SPD-2026-0005-R</strong>, el coeficiente de vulnerabilidad se ajusta dinámicamente:
            </p>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-start gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="font-bold text-emerald-400 font-mono">V = 0.5</span>
                <span><strong>Tratamiento Estándar:</strong> Colectivo general de clientes o proveedores sin datos sensibles.</span>
              </li>
              <li className="flex items-start gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="font-bold text-rose-400 font-mono">V = 0.8</span>
                <span><strong>Tratamiento Vulnerable:</strong> Datos de salud, biométricos, menores de edad o transferencias internacionales transfronterizas.</span>
              </li>
            </ul>
          </div>

          <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-800/30 text-xs text-rose-200">
            <strong>Gatillo de EIPD (PIA):</strong> Todo score $R \ge 12.0$ exige formalmente la ejecución de una Evaluación de Impacto antes de iniciar el tratamiento.
          </div>
        </div>
      </div>

      {/* ── Table: Riesgos Evaluados y Mitigaciones ───────────── */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-lg overflow-hidden space-y-3 p-6">
        <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <Layers className="w-5 h-5 text-emerald-400" />
          <span>Catálogo de Riesgos Identificados y Controles Aplicados</span>
        </h3>

        <div className="overflow-x-auto pt-2">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 uppercase font-semibold border-b border-slate-800 text-[11px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Código / Riesgo</th>
                <th className="py-3 px-4">Dimensión Afectada</th>
                <th className="py-3 px-4">Riesgo Inherente</th>
                <th className="py-3 px-4">Controles Aplicados</th>
                <th className="py-3 px-4">Riesgo Residual</th>
                <th className="py-3 px-4">Estado EIPD</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {riesgos.map((r) => {
                const scoreInherente = r.probabilidad_inherente * r.impacto_inherente * r.vulnerabilidad_coeficiente;
                const scoreResidual = r.probabilidad_residual * r.impacto_residual * r.vulnerabilidad_coeficiente;

                return (
                  <tr key={r.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-mono font-bold text-slate-200">{r.codigo}</div>
                      <div className="font-semibold text-slate-100 text-sm">{r.titulo}</div>
                    </td>
                    <td className="py-3.5 px-4 capitalize font-medium text-slate-300">
                      {r.dimension?.replace(/_/g, " ")}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-rose-400">
                      {scoreInherente.toFixed(1)} ({r.nivel_inherente})
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1 text-[11px] text-emerald-400">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>MFA + Cifrado AES-256 + DPD</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">
                      {scoreResidual.toFixed(1)} ({r.nivel_residual})
                    </td>
                    <td className="py-3.5 px-4">
                      {r.requiere_eipd ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30">
                          EIPD Obligatoria (Art. 32)
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]">No requerida</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
