"use client";

import React, { useState } from "react";
import { BookOpen, ShieldCheck, HelpCircle, Scale, Terminal } from "lucide-react";
import { useProfile } from "./ProfileContext";

interface NormativeTooltipProps {
  /** Artículo legal o resolución. Ej: "Art. 38 RGLOPDP" o "Art. 43 LOPDP" */
  articulo: string;
  /** Título o concepto. Ej: "Plazo de 5 Días Notificación SPDP" */
  titulo: string;
  /** Explicación de por qué existe este campo o métrica */
  explicacion: string;
  /** Justificación jurídica para el DPO / Auditor de la SPDP */
  justificacionLegal?: string;
  /** Criterio técnico / CISO / TI */
  criterioTecnico?: string;
  /** Riesgo o sanción por incumplimiento */
  sancionRiesgo?: string;
  /** Elemento trigger opcional (por defecto icono de ayuda) */
  children?: React.ReactNode;
}

export function NormativeTooltip({
  articulo,
  titulo,
  explicacion,
  justificacionLegal,
  criterioTecnico,
  sancionRiesgo,
  children,
}: NormativeTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { mode } = useProfile();

  return (
    <div className="relative inline-flex items-center">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        className="text-slate-400 hover:text-emerald-400 focus:outline-none transition-colors p-0.5 rounded cursor-help inline-flex items-center gap-1"
        aria-label={`Información normativa: ${titulo}`}
      >
        {children || <HelpCircle className="w-3.5 h-3.5 opacity-70 hover:opacity-100 transition-opacity" />}
      </button>

      {isOpen && (
        <div
          onMouseEnter={() => setIsOpen(true)}
          onMouseLeave={() => setIsOpen(false)}
          className="absolute z-50 bottom-full mb-2 left-1/2 -translate-x-1/2 w-80 sm:w-96 p-4 rounded-xl bg-slate-900/95 backdrop-blur-md border border-slate-700/80 shadow-2xl shadow-emerald-950/40 text-left transition-all duration-200 text-xs"
        >
          {/* Header */}
          <div className="flex items-center justify-between gap-2 pb-2 mb-2 border-b border-slate-800">
            <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
              <Scale className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{articulo}</span>
            </div>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-800/40">
              Auditoría SPDP
            </span>
          </div>

          {/* Title & Explanation */}
          <h4 className="font-semibold text-slate-100 text-sm mb-1">{titulo}</h4>
          <p className="text-slate-300 mb-3 leading-relaxed">{explicacion}</p>

          {/* Mode-Specific Rational */}
          {mode === "juridico" && justificacionLegal && (
            <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-800/30 mb-2">
              <div className="flex items-center gap-1.5 font-semibold text-emerald-300 text-[11px] mb-1">
                <BookOpen className="w-3.5 h-3.5" />
                <span>Racional para DPO / Inspector SPDP:</span>
              </div>
              <p className="text-emerald-100/90 text-[11px] leading-normal">{justificacionLegal}</p>
            </div>
          )}

          {mode === "tecnico" && criterioTecnico && (
            <div className="p-2.5 rounded-lg bg-sky-950/30 border border-sky-800/30 mb-2">
              <div className="flex items-center gap-1.5 font-semibold text-sky-300 text-[11px] mb-1">
                <Terminal className="w-3.5 h-3.5" />
                <span>Criterio CISO / Infraestructura TI:</span>
              </div>
              <p className="text-sky-100/90 text-[11px] leading-normal">{criterioTecnico}</p>
            </div>
          )}

          {/* Sancion / Risk if present */}
          {sancionRiesgo && (
            <div className="flex items-start gap-1.5 text-[10px] text-amber-300/90 pt-1">
              <ShieldCheck className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
              <span>
                <strong>Riesgo Sancionatorio:</strong> {sancionRiesgo}
              </span>
            </div>
          )}

          {/* Arrow */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px w-2 h-2 bg-slate-900 border-r border-b border-slate-700/80 rotate-45" />
        </div>
      )}
    </div>
  );
}
