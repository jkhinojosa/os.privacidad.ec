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
  ArrowRight,
  TrendingUp,
  Download,
  Activity,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Plus,
  MapPin,
  Sparkles,
  Layers,
  FileCheck,
  Shield,
  Lock,
} from "lucide-react";
import { useProfile } from "@/components/ProfileContext";
import { NormativeTooltip } from "@/components/NormativeTooltip";
import { apiFetch } from "@/lib/api";

export default function DashboardPage() {
  const { mode } = useProfile();
  const [loading, setLoading] = useState(true);
  const [slaDerechos, setSlaDerechos] = useState<any>(null);
  const [slaBrechas, setSlaBrechas] = useState<any>(null);
  const [activeDay, setActiveDay] = useState<string>("J");
  const [expandedItem, setExpandedItem] = useState<number | null>(0);

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        const [resDerechos, resBrechas] = await Promise.allSettled([
          apiFetch("/solicitudes-derechos/resumen-sla"),
          apiFetch("/brechas-seguridad/resumen-sla"),
        ]);

        if (resDerechos.status === "fulfilled") setSlaDerechos(resDerechos.value);
        if (resBrechas.status === "fulfilled") setSlaBrechas(resBrechas.value);
      } catch (err) {
        console.error("Error loading metrics:", err);
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, []);

  // Data for the lollipop chart (7 days)
  const chartDays = [
    { label: "L", value: 45, fullDay: "Lunes" },
    { label: "M", value: 65, fullDay: "Martes" },
    { label: "M", value: 55, fullDay: "Miércoles" },
    { label: "J", value: 92, fullDay: "Jueves", isCurrent: true },
    { label: "V", value: 80, fullDay: "Viernes" },
    { label: "S", value: 60, fullDay: "Sábado" },
    { label: "D", value: 50, fullDay: "Domingo" },
  ];

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* ── TOP ROW: Main Hero Card (Left) & Recent Projects Accordion (Right) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ── 1. Hero Card: Monitor de Cumplimiento & SLA LOPDP (7 Cols) ── */}
        <div className="lg:col-span-7 neo-card p-8 relative flex flex-col justify-between min-h-[440px]">
          {/* Card Header */}
          <div className="flex items-start justify-between">
            <div className="space-y-1.5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-700">
                  <Shield className="w-5 h-5" />
                </div>
                <h2 className="text-3xl font-extrabold tracking-tight text-slate-900">
                  Monitor LOPDP
                </h2>
                <NormativeTooltip
                  articulo="Capítulo III LOPDP & Art. 14 RGLOPDP"
                  titulo="Monitoreo Continuo de Plazos Perentorios"
                  explicacion="Seguimiento en tiempo real del cumplimiento de los términos de 15 días hábiles para derechos y 5 días para SPDP."
                />
              </div>
              <p className="text-xs text-slate-400 max-w-md font-normal leading-relaxed pl-13">
                Supervisión del índice de cumplimiento legal, trazabilidad y resolución de solicitudes de titulares.
              </p>
            </div>

            {/* Dropdown Filter Pill */}
            <div className="flex items-center gap-1.5 px-4 py-2 rounded-full border border-slate-200 bg-white text-xs font-semibold text-slate-700 shadow-sm cursor-pointer hover:bg-slate-50 transition-colors">
              <span>Semana</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </div>
          </div>

          {/* ── Central Lollipop / Dot Chart ── */}
          <div className="py-6 flex items-end justify-between px-6 sm:px-12 h-44 relative mt-2">
            {chartDays.map((day, idx) => {
              const isSelected = activeDay === day.label && (idx === 3 || activeDay === day.label);
              return (
                <div
                  key={idx}
                  onClick={() => setActiveDay(day.label)}
                  className="flex flex-col items-center gap-2 group cursor-pointer h-full justify-end relative"
                >
                  {/* Floating active pill badge */}
                  {isSelected && (
                    <div className="absolute -top-6 px-3 py-1 rounded-full bg-slate-900 text-white text-[11px] font-bold shadow-md shadow-slate-900/20 whitespace-nowrap animate-bounce">
                      100% SLA
                    </div>
                  )}

                  {/* Vertical Line with Dot at the Top */}
                  <div className="w-[2px] bg-slate-200 flex flex-col justify-start items-center transition-all group-hover:bg-slate-400" style={{ height: `${day.value}%` }}>
                    <div
                      className={`w-3.5 h-3.5 rounded-full -mt-1.5 transition-all ${
                        isSelected
                          ? "bg-slate-900 ring-4 ring-slate-100"
                          : "bg-sky-400 group-hover:bg-sky-500"
                      }`}
                    />
                  </div>

                  {/* Day Circle Button */}
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                      isSelected
                        ? "bg-slate-900 text-white shadow-md"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    {day.label}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Card Footer Metric */}
          <div className="pt-4 border-t border-slate-100 flex items-baseline justify-between">
            <div>
              <div className="text-4xl font-extrabold text-slate-900 tracking-tight">
                +24%
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                El índice de resolución en plazo es superior al mes anterior.
              </p>
            </div>

            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>0 Sanciones SPDP</span>
            </div>
          </div>
        </div>

        {/* ── 2. Recent Projects / Casos & Brechas (5 Cols) ──────── */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Casos & Brechas Activas
            </h3>
            <Link
              href="/dashboard/casos"
              className="text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
            >
              Ver todos los Casos
            </Link>
          </div>

          {/* Accordion Item 1: Brecha Crítica */}
          <div className="neo-card p-5 space-y-3 neo-card-hover cursor-pointer" onClick={() => setExpandedItem(expandedItem === 0 ? null : 0)}>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-2xl bg-orange-600 flex items-center justify-center text-white shadow-md shadow-orange-500/30">
                  <Flame className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-slate-900 text-sm">
                      Fuga de Credenciales DB
                    </h4>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-slate-900 text-white">
                      Notificada
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-slate-400 font-mono">
                    BRC-2026-0001 • Radicado SPDP
                  </p>
                </div>
              </div>

              <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                {expandedItem === 0 ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </div>
            </div>

            {/* Tag Pills */}
            <div className="flex flex-wrap gap-2 pt-1">
              <span className="px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-medium">
                Art. 43 LOPDP
              </span>
              <span className="px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-medium">
                5 Días Término
              </span>
              <span className="px-3 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-xs font-semibold">
                Severidad Crítica
              </span>
            </div>

            {/* Expanded Content */}
            {expandedItem === 0 && (
              <div className="pt-2 border-t border-slate-100 space-y-2 text-xs text-slate-500">
                <p className="leading-relaxed">
                  2,500 Pacientes clínicos comprometidos. Notificación radicada ante la SPDP con formulario oficial Art. 26.
                </p>
                <div className="flex items-center justify-between text-[11px] pt-1 text-slate-400">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" /> Quito, Ecuador
                  </span>
                  <span>Hace 2 horas</span>
                </div>
              </div>
            )}
          </div>

          {/* Accordion Item 2: Solicitud Rectificación */}
          <div className="neo-card p-5 space-y-3 neo-card-hover cursor-pointer" onClick={() => setExpandedItem(expandedItem === 1 ? null : 1)}>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-2xl bg-sky-600 flex items-center justify-center text-white shadow-md shadow-sky-500/30">
                  <Users2 className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-slate-900 text-sm">
                      Rectificación SOL-2026-0002
                    </h4>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                      En Plazo
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 font-mono">
                    Art. 23 RGLOPDP Encargados
                  </p>
                </div>
              </div>

              <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                {expandedItem === 1 ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </div>
            </div>

            {expandedItem === 1 && (
              <div className="pt-2 border-t border-slate-100 text-xs text-slate-500 leading-relaxed">
                Orden formal de réplica emitida al proveedor tecnológico para actualizar datos bancarios.
              </div>
            )}
          </div>

          {/* Accordion Item 3: EIPD Aprobada */}
          <div className="neo-card p-5 space-y-3 neo-card-hover cursor-pointer" onClick={() => setExpandedItem(expandedItem === 2 ? null : 2)}>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-2xl bg-teal-600 flex items-center justify-center text-white shadow-md shadow-teal-500/30">
                  <FileCheck className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-slate-900 text-sm">
                      Evaluación EIPD-2026-0001
                    </h4>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-slate-900 text-white">
                      Aprobada
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 font-mono">
                    Res. SPDP-SPD-2026-0005-R
                  </p>
                </div>
              </div>

              <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                {expandedItem === 2 ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </div>
            </div>

            {expandedItem === 2 && (
              <div className="pt-2 border-t border-slate-100 text-xs text-slate-500 leading-relaxed">
                Dictamen favorable emitido para el tratamiento de telemedicina a gran escala.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── BOTTOM ROW: 3 Distinct Cards ──────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch">
        {/* ── 1. Let's Connect / Equipo DPD & CISO (4 Cols) ─────── */}
        <div className="md:col-span-4 neo-card p-6 space-y-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-extrabold text-slate-900 tracking-tight">
              Equipo de Privacidad
            </h3>
            <span className="text-xs font-semibold text-slate-400">Ver todo</span>
          </div>

          <div className="space-y-3">
            {/* Member 1 */}
            <div className="flex items-center justify-between p-2 rounded-2xl hover:bg-slate-50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-xs">
                  RG
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h5 className="font-bold text-slate-900 text-xs">Randy Gouse</h5>
                    <span className="px-2 py-0.2 rounded-full text-[9px] font-extrabold uppercase bg-rose-600 text-white">
                      DPD
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">Delegado de Protección de Datos</p>
                </div>
              </div>
              <button className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-900 hover:text-white flex items-center justify-center text-slate-700 transition-colors">
                <Plus className="w-4 h-4" />
              </button>
            </div>

            {/* Member 2 */}
            <div className="flex items-center justify-between p-2 rounded-2xl hover:bg-slate-50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-sky-700 text-white flex items-center justify-center font-bold text-xs">
                  GS
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h5 className="font-bold text-slate-900 text-xs">Giana Schleifer</h5>
                    <span className="px-2 py-0.2 rounded-full text-[9px] font-extrabold uppercase bg-sky-600 text-white">
                      CISO
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">Oficial de Seguridad TI</p>
                </div>
              </div>
              <button className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-900 hover:text-white flex items-center justify-center text-slate-700 transition-colors">
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* ── 2. Unlock Premium / Auditoría SPDP 2026 (4 Cols) ───── */}
        <div className="md:col-span-4 rounded-3xl p-6 relative overflow-hidden bg-gradient-to-br from-slate-200 via-slate-100 to-slate-200 border border-slate-300 flex flex-col justify-between shadow-sm">
          {/* Halftone / Dot pattern background effect */}
          <div className="absolute right-0 bottom-0 opacity-15 pointer-events-none text-slate-800 text-9xl font-mono select-none leading-none">
            🛡️
          </div>

          <div className="space-y-2 relative z-10">
            <h4 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Auditoría SPDP 2026
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed max-w-xs">
              Expediente probatorio inmutable de <em>Accountability</em> listo para inspecciones regulatorias.
            </p>
          </div>

          <div className="pt-6 relative z-10">
            <button
              onClick={() => window.print()}
              className="w-full py-3 px-5 rounded-full bg-white hover:bg-slate-900 hover:text-white text-slate-900 text-xs font-bold transition-all shadow-md flex items-center justify-between group"
            >
              <span>Generar Informe Consolidado</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>

        {/* ── 3. Proposal Progress / Métricas de Respuesta (4 Cols) ─ */}
        <div className="md:col-span-4 neo-card p-6 space-y-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-extrabold text-slate-900 tracking-tight">
              Métricas Legales
            </h3>
            <div className="flex items-center gap-1 text-xs font-semibold text-slate-500 cursor-pointer">
              <span>Agosto 2026</span>
              <ChevronDown className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* 3 Columns metrics */}
          <div className="grid grid-cols-3 gap-2 text-left pt-1">
            <div>
              <span className="text-[10px] font-semibold text-slate-400 block truncate">
                RAT Registrados
              </span>
              <span className="text-2xl font-extrabold text-slate-900">3</span>
            </div>
            <div>
              <span className="text-[10px] font-semibold text-slate-400 block truncate">
                SLA Derechos
              </span>
              <span className="text-2xl font-extrabold text-slate-900">100%</span>
            </div>
            <div>
              <span className="text-[10px] font-semibold text-slate-400 block truncate">
                Brechas SPDP
              </span>
              <span className="text-2xl font-extrabold text-slate-900">100%</span>
            </div>
          </div>

          {/* Barcode / Stripe progress meter from reference mockup */}
          <div className="pt-2 flex items-center gap-1 h-12">
            {/* Section 1: Grey stripes (Proposals) */}
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={`g1-${i}`} className="flex-1 h-8 bg-slate-200 rounded-full" />
            ))}
            {/* Section 2: Orange active stripes (Interviews) */}
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={`o-${i}`} className="flex-1 h-10 bg-orange-600 rounded-full" />
            ))}
            {/* Section 3: Dark navy stripes (Hires) */}
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={`g2-${i}`} className="flex-1 h-8 bg-slate-900 rounded-full" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
