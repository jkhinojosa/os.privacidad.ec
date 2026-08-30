"use client";

import React, { useState, useEffect } from "react";
import {
  Flame,
  Plus,
  Clock,
  Download,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Building2,
  Calendar,
  Eye,
  ShieldCheck,
  Scale,
  X,
} from "lucide-react";
import { NormativeTooltip } from "@/components/NormativeTooltip";
import { apiFetch } from "@/lib/api";

export default function BrechasPage() {
  const [brechas, setBrechas] = useState<any[]>([]);
  const [resumenSla, setResumenSla] = useState<any>(null);
  const [selectedInforme, setSelectedInforme] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [resBrechas, resSla] = await Promise.allSettled([
          apiFetch<any[]>("/brechas-seguridad"),
          apiFetch<any>("/brechas-seguridad/resumen-sla"),
        ]);
        if (resBrechas.status === "fulfilled") setBrechas(resBrechas.value);
        if (resSla.status === "fulfilled") setResumenSla(resSla.value);
      } catch (err) {
        console.error("Error loading brechas:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const verInformeOficial = async (id: string) => {
    try {
      const informe = await apiFetch<any>(`/brechas-seguridad/${id}/informe-spdp`);
      setSelectedInforme(informe);
    } catch (err) {
      console.error("Error cargando informe SPDP:", err);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* ── Header ────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-100">
              Centro de Mando: Brechas & Notificaciones SPDP
            </h1>
            <NormativeTooltip
              articulo="Art. 43 y 46 LOPDP & Arts. 24-28 RGLOPDP"
              titulo="Notificación de Vulneraciones de Seguridad"
              explicacion="Plazo fatal de 5 días hábiles ante la SPDP y ARCOTEL. Plazo fatal de 3 días hábiles ante titulares si existe riesgo a derechos fundamentales."
              justificacionLegal="La pronta reacción y el informe formal con los 7 requisitos del Art. 26 constituyen atenuantes legales explícitos ante la autoridad."
              criterioTecnico="Integración con ISO/IEC 27035: Contención inmediata, erradicación de causa raíz y conservación de logs para auditoría forense."
            />
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Gestión de incidentes, cronómetros perentorios de 5 días SPDP / 3 días Titulares e Informes Oficiales Art. 26.
          </p>
        </div>

        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-slate-100 text-xs font-bold transition-all shadow-lg shadow-rose-950/50">
          <Plus className="w-4 h-4" />
          <span>Reportar Nueva Brecha de Seguridad</span>
        </button>
      </div>

      {/* ── KPI Cards: Plazos SPDP & Titulares ─────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400">Total Vulneraciones</span>
          <p className="text-2xl font-bold text-slate-100">{resumenSla?.total_brechas || brechas.length}</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-emerald-900/40 space-y-1">
          <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> SPDP en Plazo (≤ 5d)
          </span>
          <p className="text-2xl font-bold text-emerald-300">{resumenSla?.spdp_en_tiempo || 1}</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-teal-900/40 space-y-1">
          <span className="text-xs font-semibold text-teal-400 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" /> Notificadas a SPDP
          </span>
          <p className="text-2xl font-bold text-teal-300">{resumenSla?.notificadas_a_spdp || 1}</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-amber-900/40 space-y-1">
          <span className="text-xs font-semibold text-amber-400 flex items-center gap-1">
            <Scale className="w-3.5 h-3.5" /> Notificadas a Titulares (≤ 3d)
          </span>
          <p className="text-2xl font-bold text-amber-300">{resumenSla?.notificadas_a_titulares || 1}</p>
        </div>
      </div>

      {/* ── Brechas Table ─────────────────────────────────────── */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-lg overflow-hidden space-y-3 p-6">
        <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <Flame className="w-5 h-5 text-rose-400" />
          <span>Incidentes de Vulneración Registrados</span>
        </h3>

        <div className="overflow-x-auto pt-2">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 uppercase font-semibold border-b border-slate-800 text-[11px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Código / Incidente</th>
                <th className="py-3 px-4">Tipo & Severidad</th>
                <th className="py-3 px-4">Estado Proceso</th>
                <th className="py-3 px-4">Plazo SPDP (5d)</th>
                <th className="py-3 px-4">Plazo Titulares (3d)</th>
                <th className="py-3 px-4 text-right">Informe Art. 26</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {brechas.map((b) => (
                <tr key={b.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-4 px-4">
                    <div className="font-mono font-bold text-rose-400">{b.codigo}</div>
                    <div className="font-semibold text-slate-100 text-sm">{b.titulo}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      {b.volumen_titulares_estimado?.toLocaleString()} titulares • {b.sistemas_afectados}
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="space-y-1">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 uppercase block w-fit">
                        {b.severidad}
                      </span>
                      <span className="text-[11px] text-slate-400 capitalize block">
                        Vulneración de {b.tipo_vulneracion}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-teal-950 text-teal-300 border border-teal-800 uppercase">
                      {b.estado?.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <div className="font-mono text-[11px]">
                      {b.notificada_a_spdp ? (
                        <div>
                          <span className="text-emerald-400 font-bold">✓ Notificada Formalmente</span>
                          <p className="text-[10px] text-slate-400">{b.numero_radicado_spdp}</p>
                        </div>
                      ) : (
                        <span className="text-amber-400 font-bold">
                          {b.dias_restantes_spdp}d restantes
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="font-mono text-[11px]">
                      {b.notificada_a_titulares ? (
                        <span className="text-emerald-400 font-bold">✓ Notificados (Art. 46)</span>
                      ) : b.requiere_notificacion_titulares ? (
                        <span className="text-amber-400 font-bold">
                          {b.dias_restantes_titulares}d restantes
                        </span>
                      ) : (
                        <span className="text-slate-500">No aplica riesgo</span>
                      )}
                    </div>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <button
                      onClick={() => verInformeOficial(b.id)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-emerald-400 transition-colors shadow-sm"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Ver Informe SPDP</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Modal: Informe Oficial Art. 26 RGLOPDP ─────────────── */}
      {selectedInforme && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-fadeIn">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-400" />
                <h3 className="font-bold text-slate-100 text-base">
                  Informe Técnico Oficial de Notificación (Art. 26 RGLOPDP)
                </h3>
              </div>
              <button
                onClick={() => setSelectedInforme(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body: Markdown Renderer */}
            <div className="p-6 overflow-y-auto font-mono text-xs text-slate-300 space-y-4 whitespace-pre-wrap leading-relaxed bg-slate-950/60">
              {selectedInforme.informe_markdown}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                Código: <strong>{selectedInforme.codigo}</strong> • 7 Numerales Mínimos
              </span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(selectedInforme.informe_markdown);
                  alert("Informe copiado al portapapeles listo para radicación ante la SPDP.");
                }}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-slate-950 text-xs font-bold transition-colors"
              >
                Copiar Texto Oficial para SPDP
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
