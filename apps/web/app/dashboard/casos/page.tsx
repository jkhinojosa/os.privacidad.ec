"use client";

import React, { useState, useEffect } from "react";
import {
  FolderLock,
  Plus,
  ArrowRight,
  ShieldCheck,
  FileText,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { NormativeTooltip } from "@/components/NormativeTooltip";
import { apiFetch } from "@/lib/api";

export default function CasosPage() {
  const [casos, setCasos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadCasos() {
      try {
        setLoading(true);
        const data = await apiFetch<any[]>("/casos");
        setCasos(data);
      } catch (err) {
        console.error("Error loading casos:", err);
      } finally {
        setLoading(false);
      }
    }
    loadCasos();
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* ── Header ────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-100">
              Casos & Expedientes de Auditoría LOPDP
            </h1>
            <NormativeTooltip
              articulo="Principio de Responsabilidad Proactiva (Art. 10 LOPDP)"
              titulo="Trazabilidad e Inmutabilidad de Expedientes"
              explicacion="Cada caso organiza la investigación, evidencias forenses, dictámenes del DPD y decisiones del Comité de Privacidad bajo una máquina de estados determinista."
              justificacionLegal="Sustento probatorio de la debida diligencia de la organización ante requerimientos de información o procedimientos sancionatorios de la SPDP."
            />
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Gestión procesal con máquina de estados estricta (Abierto → En Investigación → En Comité → Cerrado).
          </p>
        </div>

        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-slate-100 text-xs font-bold transition-all shadow-lg shadow-purple-950/50">
          <Plus className="w-4 h-4" />
          <span>Aperturar Nuevo Caso</span>
        </button>
      </div>

      {/* ── Casos Grid ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {casos.map((c) => (
          <div
            key={c.id}
            className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-purple-500/40 transition-all shadow-lg space-y-4 flex flex-col justify-between"
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-purple-300 text-xs">{c.codigo}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20 uppercase">
                  {c.estado?.replace(/_/g, " ")}
                </span>
              </div>
              <h3 className="font-bold text-slate-100 text-sm">{c.titulo}</h3>
              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{c.descripcion}</p>
            </div>

            <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
              <span className="capitalize font-mono">Prioridad: <strong>{c.prioridad}</strong></span>
              <span className="text-purple-400 font-semibold flex items-center gap-1">
                <span>Ver Expediente</span>
                <ArrowRight className="w-3 h-3" />
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
