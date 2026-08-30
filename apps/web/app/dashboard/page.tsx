"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FileSpreadsheet,
  AlertTriangle,
  Users2,
  Flame,
  ShieldCheck,
  Clock,
  ArrowUpRight,
  TrendingUp,
  Download,
  Activity,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  FileCheck,
} from "lucide-react";
import { useProfile } from "@/components/ProfileContext";
import { NormativeTooltip } from "@/components/NormativeTooltip";
import { apiFetch } from "@/lib/api";

export default function DashboardPage() {
  const { mode } = useProfile();
  const [loading, setLoading] = useState(true);
  const [slaDerechos, setSlaDerechos] = useState<any>(null);
  const [slaBrechas, setSlaBrechas] = useState<any>(null);
  const [matrizRiesgos, setMatrizRiesgos] = useState<any>(null);

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        // Cargar métricas en paralelo
        const [resDerechos, resBrechas, resMatriz] = await Promise.allSettled([
          apiFetch("/solicitudes-derechos/resumen-sla"),
          apiFetch("/brechas-seguridad/resumen-sla"),
          apiFetch("/riesgos/matriz"),
        ]);

        if (resDerechos.status === "fulfilled") setSlaDerechos(resDerechos.value);
        if (resBrechas.status === "fulfilled") setSlaBrechas(resBrechas.value);
        if (resMatriz.status === "fulfilled") setMatrizRiesgos(resMatriz.value);
      } catch (err) {
        console.error("Error loading metrics:", err);
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-100">
              Dashboard de Gobernanza & Auditoría
            </h1>
            <span
              className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
                mode === "juridico"
                  ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/20"
                  : "bg-sky-500/10 text-sky-300 border-sky-500/20"
              }`}
            >
              {mode === "juridico" ? "Vista DPO / Legal" : "Vista CISO / TI"}
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Supervisión integral de cumplimiento LOPDP 2026, métricas de riesgo y plazos perentorios ante la SPDP.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => window.print()}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors shadow-sm"
          >
            <Download className="w-4 h-4 text-emerald-400" />
            <span>Exportar Informe Auditoría SPDP</span>
          </button>
        </div>
      </div>

      {/* ── KPI Executive Cards ─────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        {/* Card 1: RAT Procesos */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>Inventario RAT</span>
              <NormativeTooltip
                articulo="Art. 38 RGLOPDP"
                titulo="Registro de Actividades de Tratamiento (RAT)"
                explicacion="Inventario obligatorio y permanente de todos los tratamientos de datos personales gestionados por el responsable."
                justificacionLegal="La LOPDP y su Reglamento exigen documentar los 9 campos obligatorios para cada proceso. No mantener el RAT actualizado acarrea infracciones graves."
                criterioTecnico="Mapeo de arquitectura de datos y repositorios para identificar bases de datos con datos personales."
                sancionRiesgo="Multa grave hasta 0.7% del volumen de negocio."
              />
            </span>
            <div className="w-8 h-8 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center">
              <FileSpreadsheet className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-slate-100">3</span>
            <span className="text-xs font-medium text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> 100% 9 Campos
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Procesos mapeados con base legal activa (Art. 7 LOPDP).
          </p>
        </div>

        {/* Card 2: Riesgo Promedio */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>Riesgo Global</span>
              <NormativeTooltip
                articulo="Res. SPDP-SPD-2026-0005-R"
                titulo="Metodología de Riesgos R = P × (I × V)"
                explicacion="Fórmula matemática oficial de ponderación donde V=0.8 aplica obligatoriamente a grupos vulnerables, menores o salud."
                justificacionLegal="Obligación legal de evaluar el impacto en derechos y libertades de los titulares previo al tratamiento."
                criterioTecnico="Score ponderado cuantitativo de 1 a 25. Scores ≥ 12 gatillan obligatoriamente EIPD."
              />
            </span>
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-amber-300">Medio</span>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800/40">
              Score: 9.6
            </span>
          </div>
          <p className="text-xs text-slate-400">
            2 Riesgos mitigados • 1 EIPD obligatoria requerida.
          </p>
        </div>

        {/* Card 3: SLA Derechos Titulares */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>SLA Derechos LOPDP</span>
              <NormativeTooltip
                articulo="Art. 14 RGLOPDP"
                titulo="Plazo Perentorio de 15 Días Hábiles"
                explicacion="Tiempo límite legal para atender solicitudes de Acceso, Rectificación, Eliminación, Oposición, Portabilidad y Suspensión."
                justificacionLegal="Término estricto en días hábiles. Prórroga de 15 días adicionales requiere justificación técnica de complejidad."
                criterioTecnico="Cómputo en días hábiles excluyendo sábados, domingos y feriados nacionales ecuatorianos."
                sancionRiesgo="Infracción grave por denegación tácita del derecho."
              />
            </span>
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Users2 className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-emerald-400">
              {slaDerechos?.porcentaje_cumplimiento || 100}%
            </span>
            <span className="text-xs font-medium text-emerald-400 flex items-center gap-1 font-mono">
              <Clock className="w-3.5 h-3.5" /> 15d Hábiles
            </span>
          </div>
          <p className="text-xs text-slate-400">
            {slaDerechos?.total_solicitudes || 3} Solicitudes • 0 Vencidas.
          </p>
        </div>

        {/* Card 4: SLA Brechas SPDP */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>Brechas SPDP</span>
              <NormativeTooltip
                articulo="Art. 43 LOPDP & Art. 24 RGLOPDP"
                titulo="Término de 5 Días Notificación SPDP"
                explicacion="Plazo fatal de 5 días hábiles para notificar incidentes de seguridad que afecten datos personales a la SPDP y ARCOTEL."
                justificacionLegal="Notificar dentro del término legal es un atenuante formal ante procedimientos sancionatorios. Vencido el plazo exige justificar dilación."
                criterioTecnico="Respuesta a incidentes ISO/IEC 27035 y contención inmediata para evitar fuga masiva."
              />
            </span>
            <div className="w-8 h-8 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-rose-400">
              {slaBrechas?.porcentaje_cumplimiento_spdp || 100}%
            </span>
            <span className="text-xs font-medium text-slate-400 font-mono">
              5d SPDP / 3d Tit.
            </span>
          </div>
          <p className="text-xs text-slate-400">
            {slaBrechas?.total_brechas || 1} Incidente notificado con radicado formal.
          </p>
        </div>
      </div>

      {/* ── Main Dashboard Content Grid ────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Matriz de Calor 5x5 & Control Preventivo */}
        <div className="lg:col-span-2 space-y-6">
          {/* Matriz 5x5 Widget */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-lg space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-slate-100">
                  Matriz de Calor de Riesgos LOPDP (5 × 5)
                </h3>
                <NormativeTooltip
                  articulo="Guía de Riesgos SPDP 2026"
                  titulo="Ponderación de Probabilidad vs Impacto"
                  explicacion="Visualización bidimensional del riesgo inherente y residual tras aplicar controles de seguridad (técnicos, organizativos y jurídicos)."
                  justificacionLegal="Exigencia de la autoridad para clasificar operaciones de tratamiento de alto riesgo."
                />
              </div>
              <Link
                href="/dashboard/riesgos"
                className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-colors"
              >
                <span>Ver Detalle Completo</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Matriz Grid Mini */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 space-y-2">
              <div className="grid grid-cols-5 gap-1.5 text-center text-[10px] font-mono">
                {[5, 4, 3, 2, 1].map((prob) =>
                  [1, 2, 3, 4, 5].map((imp) => {
                    const score = prob * imp * 0.5;
                    let bgColor = "bg-emerald-950/40 text-emerald-400 border-emerald-900/30";
                    if (score >= 8 && score < 12) bgColor = "bg-amber-950/40 text-amber-300 border-amber-900/30";
                    if (score >= 12) bgColor = "bg-rose-950/40 text-rose-400 border-rose-900/30";

                    return (
                      <div
                        key={`${prob}-${imp}`}
                        className={`h-9 rounded-lg border flex flex-col items-center justify-center transition-transform hover:scale-105 cursor-pointer ${bgColor}`}
                        title={`P: ${prob}, I: ${imp} • Score: ${score.toFixed(1)}`}
                      >
                        <span className="font-bold">{score.toFixed(1)}</span>
                      </div>
                    );
                  })
                )}
              </div>
              <div className="flex justify-between text-[11px] text-slate-400 pt-2 font-mono">
                <span>Impacto → (1 a 5)</span>
                <span>Probabilidad ↑ (1 a 5)</span>
              </div>
            </div>
          </div>

          {/* SLA Derechos Preview */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-lg space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users2 className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-slate-100">
                  Solicitudes de Derechos de Titulares Recientes
                </h3>
                <NormativeTooltip
                  articulo="Capítulo III LOPDP"
                  titulo="Catálogo Oficial de Derechos Digitales"
                  explicacion="Reemplaza formalmente la denominación foránea ARCO por el catálogo ecuatoriano (Acceso, Rectificación, Supresión, Oposición, Portabilidad, Suspensión)."
                />
              </div>
              <Link
                href="/dashboard/derechos"
                className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-colors"
              >
                <span>Bandeja de Entrada</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-2">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-200">SOL-2026-0001</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                      Acceso (Art. 13)
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px] mt-0.5">Dra. María Elena Dávila • Formulario Web</p>
                </div>
                <div className="text-right font-mono">
                  <span className="px-2 py-1 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800 text-[11px] font-bold">
                    14 días hábiles restantes
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-200">SOL-2026-0002</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-teal-500/10 text-teal-300 border border-teal-500/20">
                      Rectificación (Art. 14)
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px] mt-0.5">Lic. Juan Carlos Paredes • Notificado a Encargado Art. 23</p>
                </div>
                <div className="text-right font-mono">
                  <span className="px-2 py-1 rounded bg-teal-950/80 text-teal-300 border border-teal-800 text-[11px] font-bold">
                    Notificada Encargado
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Incidentes de Seguridad & Compliance Status */}
        <div className="space-y-6">
          {/* Incidentes Recientes */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-lg space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Flame className="w-5 h-5 text-rose-400" />
                <h3 className="text-base font-bold text-slate-100">
                  Brechas & Notificaciones SPDP
                </h3>
                <NormativeTooltip
                  articulo="Art. 26 RGLOPDP"
                  titulo="Informe Técnico de 7 Numerales"
                  explicacion="Cada brecha genera automáticamente el informe oficial listo para radicar ante la Superintendencia."
                />
              </div>
              <Link
                href="/dashboard/brechas"
                className="text-xs font-semibold text-rose-400 hover:text-rose-300 flex items-center gap-1 transition-colors"
              >
                <span>Gestión Brechas</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-rose-950/80 space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-rose-300">BRC-2026-0001</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  Severidad Crítica
                </span>
              </div>
              <h4 className="font-semibold text-slate-200">
                Fuga de Credenciales y Tráfico Anómalo Outbound
              </h4>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                2,500 Pacientes comprometidos. Notificada formalmente a la SPDP con radicado <code>SPDP-EXP-2026-004412-E</code>.
              </p>
              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px]">
                <span className="text-emerald-400 font-medium">✓ Notificada en Plazo</span>
                <Link
                  href="/dashboard/brechas"
                  className="text-rose-400 hover:underline font-semibold"
                >
                  Descargar Informe Art. 26 →
                </Link>
              </div>
            </div>
          </div>

          {/* Checklist Auditoría SPDP */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900/90 to-emerald-950/30 border border-emerald-800/40 shadow-lg space-y-3">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
              <FileCheck className="w-4 h-4" />
              <span>Inspección Regulatoria SPDP</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              El entorno cumple al 100% con los principios de <strong>Responsabilidad Proactiva (Accountability)</strong> exigidos por la Superintendencia de Protección de Datos Personales del Ecuador.
            </p>
            <ul className="space-y-1.5 text-xs text-slate-300 pt-1">
              <li className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Base de Datos PostgreSQL con Aislamiento RLS</span>
              </li>
              <li className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Cálculo de Plazos en Días Hábiles Ecuatorianos</span>
              </li>
              <li className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Audit Trail Inmutable de Operaciones</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
