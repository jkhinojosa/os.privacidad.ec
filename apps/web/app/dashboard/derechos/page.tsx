"use client";

import React, { useState, useEffect } from "react";
import {
  Users2,
  Plus,
  Clock,
  Download,
  Send,
  AlertCircle,
  CheckCircle2,
  FileText,
  Building2,
  Calendar,
  ExternalLink,
} from "lucide-react";
import { NormativeTooltip } from "@/components/NormativeTooltip";
import { apiFetch, API_URL, getAccessToken } from "@/lib/api";

export default function DerechosPage() {
  const [solicitudes, setSolicitudes] = useState<any[]>([]);
  const [resumenSla, setResumenSla] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [resSols, resSla] = await Promise.allSettled([
          apiFetch<any[]>("/solicitudes-derechos"),
          apiFetch<any>("/solicitudes-derechos/resumen-sla"),
        ]);
        if (resSols.status === "fulfilled") setSolicitudes(resSols.value);
        if (resSla.status === "fulfilled") setResumenSla(resSla.value);
      } catch (err) {
        console.error("Error loading solicitudes:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const downloadPortabilidad = (id: string, formato: "json" | "csv") => {
    const token = getAccessToken();
    const url = `${API_URL}/solicitudes-derechos/${id}/exportar-portabilidad?formato=${formato}`;
    window.open(url, "_blank");
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* ── Header ────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-100">
              Catálogo de Derechos de los Titulares
            </h1>
            <NormativeTooltip
              articulo="Capítulo III LOPDP (Arts. 12-24) & Art. 14 RGLOPDP"
              titulo="Catálogo Oficial de Derechos Digitales"
              explicacion="Reemplaza formalmente la denominación foránea ARCO por el catálogo oficial ecuatoriano: Acceso (Art. 13), Rectificación (Art. 14), Eliminación (Art. 15), Oposición (Art. 16), Portabilidad (Art. 17), Suspensión (Art. 19)."
              justificacionLegal="Término perentorio de 15 días hábiles para responder. La prórroga de 15 días adicionales requiere dictamen justificado del DPD."
              criterioTecnico="Replicación obligatoria a encargados del tratamiento (Art. 23 Reglamento) y exportación interoperable en JSON y CSV."
            />
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Recepción, sustanciación, prórrogas, cómputo en días hábiles y réplica a encargados (Art. 23 RGLOPDP).
          </p>
        </div>

        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-emerald-950/50">
          <Plus className="w-4 h-4" />
          <span>Radicar Nueva Solicitud</span>
        </button>
      </div>

      {/* ── SLA Metric Cards ──────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400">Total Solicitudes</span>
          <p className="text-2xl font-bold text-slate-100">{resumenSla?.total_solicitudes || solicitudes.length}</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-emerald-900/40 space-y-1">
          <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> En Tiempo (&gt; 3d hábiles)
          </span>
          <p className="text-2xl font-bold text-emerald-300">{resumenSla?.en_tiempo || 2}</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-amber-900/40 space-y-1">
          <span className="text-xs font-semibold text-amber-400 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" /> En Alerta (1 a 3d hábiles)
          </span>
          <p className="text-2xl font-bold text-amber-300">{resumenSla?.en_alerta || 0}</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-rose-900/40 space-y-1">
          <span className="text-xs font-semibold text-rose-400 flex items-center gap-1">
            <AlertCircle className="w-3.5 h-3.5" /> Vencidas / Fuera de Plazo
          </span>
          <p className="text-2xl font-bold text-rose-300">{resumenSla?.vencidas || 0}</p>
        </div>
      </div>

      {/* ── Requests Table ────────────────────────────────────── */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-lg overflow-hidden space-y-3 p-6">
        <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <Users2 className="w-5 h-5 text-emerald-400" />
          <span>Bandeja de Entrada de Solicitudes LOPDP</span>
        </h3>

        <div className="overflow-x-auto pt-2">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 uppercase font-semibold border-b border-slate-800 text-[11px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Código / Titular</th>
                <th className="py-3 px-4">Tipo de Derecho</th>
                <th className="py-3 px-4">Estado Procesal</th>
                <th className="py-3 px-4">SLA Días Hábiles</th>
                <th className="py-3 px-4">Órdenes Encargados</th>
                <th className="py-3 px-4 text-right">Acciones / Portabilidad</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {solicitudes.map((s) => {
                let badgeEstado = "bg-slate-800 text-slate-300 border-slate-700";
                if (s.estado === "recibida") badgeEstado = "bg-blue-500/10 text-blue-300 border-blue-500/20";
                if (s.estado === "aprobada" || s.estado === "atendida") badgeEstado = "bg-emerald-500/10 text-emerald-300 border-emerald-500/20";
                if (s.estado === "notificada_encargados") badgeEstado = "bg-teal-500/10 text-teal-300 border-teal-500/20";
                if (s.estado === "denegada") badgeEstado = "bg-rose-500/10 text-rose-300 border-rose-500/20";

                return (
                  <tr key={s.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-4 px-4">
                      <div className="font-mono font-bold text-slate-200">{s.codigo}</div>
                      <div className="font-semibold text-slate-100 text-sm">{s.titular_nombre}</div>
                      <div className="text-[11px] text-slate-400 font-mono">CI: {s.titular_identificacion}</div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 uppercase">
                        {s.tipo_derecho?.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`px-2.5 py-1 rounded-lg text-[11px] font-bold border uppercase ${badgeEstado}`}>
                        {s.estado?.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="font-mono text-[11px]">
                        <span className="font-bold text-emerald-400">
                          {s.dias_restantes_habiles !== undefined ? `${s.dias_restantes_habiles}d restantes` : "Atendida"}
                        </span>
                        <p className="text-[10px] text-slate-400">
                          Límite: {new Date(s.fecha_limite_sla).toLocaleDateString("es-EC")}
                        </p>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      {s.notificaciones_encargados && s.notificaciones_encargados.length > 0 ? (
                        <div className="space-y-1">
                          {s.notificaciones_encargados.map((n: any) => (
                            <span
                              key={n.id}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-teal-950/60 text-teal-300 border border-teal-800"
                            >
                              <Building2 className="w-3 h-3" />
                              <span>{n.encargado_nombre}</span>
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-500 text-[11px]">Sin encargados</span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right space-x-2 font-mono">
                      {s.tipo_derecho === "portabilidad" && (
                        <div className="inline-flex gap-1">
                          <button
                            onClick={() => downloadPortabilidad(s.id, "json")}
                            className="px-2 py-1 rounded bg-slate-950 border border-slate-700 hover:border-emerald-500 text-[10px] font-bold text-emerald-400 transition-colors"
                          >
                            JSON
                          </button>
                          <button
                            onClick={() => downloadPortabilidad(s.id, "csv")}
                            className="px-2 py-1 rounded bg-slate-950 border border-slate-700 hover:border-emerald-500 text-[10px] font-bold text-teal-400 transition-colors"
                          >
                            CSV
                          </button>
                        </div>
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
