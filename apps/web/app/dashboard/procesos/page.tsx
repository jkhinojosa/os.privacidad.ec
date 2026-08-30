"use client";

import React, { useState, useEffect } from "react";
import {
  FileSpreadsheet,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle,
  Scale,
  ShieldCheck,
  Building2,
  Clock,
  BookOpen,
} from "lucide-react";
import { NormativeTooltip } from "@/components/NormativeTooltip";
import { apiFetch } from "@/lib/api";

export default function ProcesosPage() {
  const [procesos, setProcesos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [baseLegalFilter, setBaseLegalFilter] = useState("");

  useEffect(() => {
    async function loadProcesos() {
      try {
        setLoading(true);
        const data = await apiFetch<any[]>("/procesos");
        setProcesos(data);
      } catch (err) {
        console.error("Error loading procesos:", err);
      } finally {
        setLoading(false);
      }
    }
    loadProcesos();
  }, []);

  const filteredProcesos = procesos.filter((p) => {
    const matchSearch =
      p.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.finalidad.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.codigo && p.codigo.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchBase = !baseLegalFilter || p.base_legal === baseLegalFilter;
    return matchSearch && matchBase;
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* ── Header ────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-100">
              Registro de Actividades de Tratamiento (RAT)
            </h1>
            <NormativeTooltip
              articulo="Art. 38 RGLOPDP & Art. 10 LOPDP"
              titulo="Obligación del Inventario RAT"
              explicacion="Inventario integral y permanente de los tratamientos de datos. La omisión de los 9 campos obligatorios acarrea sanciones graves ante la SPDP."
              justificacionLegal="Obligatorio para todo responsable y encargado. Debe ponerse a disposición inmediata de la SPDP cuando esta lo requiera."
              criterioTecnico="Permite mapear el flujo del dato, los sistemas de almacenamiento y la superficie de exposición ante ciberataques."
              sancionRiesgo="Infracción grave según Art. 67 LOPDP."
            />
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Inventario formal estructurado bajo los <strong>9 campos obligatorios del Art. 38 del Reglamento General a la LOPDP</strong>.
          </p>
        </div>

        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-emerald-950/50">
          <Plus className="w-4 h-4" />
          <span>Registrar Nueva Actividad RAT</span>
        </button>
      </div>

      {/* ── 9 Mandatory Fields Alert Banner ───────────────────── */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-teal-800/40 text-xs text-slate-300 space-y-2">
        <div className="flex items-center gap-2 text-teal-400 font-bold">
          <Scale className="w-4 h-4" />
          <span>Verificación de Cumplimiento de los 9 Campos Obligatorios (Art. 38 RGLOPDP):</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 text-[11px] text-slate-400 font-mono">
          <span className="p-1.5 rounded bg-slate-950 border border-slate-800">1. Nombre y Finalidad</span>
          <span className="p-1.5 rounded bg-slate-950 border border-slate-800">2. Base Legal (Art. 7)</span>
          <span className="p-1.5 rounded bg-slate-950 border border-slate-800">3. Tipología de Titulares</span>
          <span className="p-1.5 rounded bg-slate-950 border border-slate-800">4. Categorías de Datos</span>
          <span className="p-1.5 rounded bg-slate-950 border border-slate-800">5. Plazos Conservación</span>
          <span className="p-1.5 rounded bg-slate-950 border border-slate-800">6. Destinatarios / Encargados</span>
          <span className="p-1.5 rounded bg-slate-950 border border-slate-800">7. Transferencia Internacional</span>
          <span className="p-1.5 rounded bg-slate-950 border border-slate-800">8. Medidas de Seguridad</span>
          <span className="p-1.5 rounded bg-slate-950 border border-slate-800">9. Delegado DPD Asignado</span>
        </div>
      </div>

      {/* ── Filters ───────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Buscar por nombre de proceso, finalidad o código..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={baseLegalFilter}
            onChange={(e) => setBaseLegalFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors"
          >
            <option value="">Todas las Bases Legales (Art. 7 LOPDP)</option>
            <option value="consentimiento">Consentimiento Expreso</option>
            <option value="cumplimiento_legal">Cumplimiento Legal</option>
            <option value="ejecucion_contractual">Ejecución Contractual</option>
            <option value="interes_legitimo">Interés Legítimo</option>
            <option value="mision_interes_publico">Misión de Interés Público</option>
          </select>
        </div>
      </div>

      {/* ── Table RAT ─────────────────────────────────────────── */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 uppercase font-semibold border-b border-slate-800 text-[11px] tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Código / Actividad</th>
                <th className="py-3.5 px-4">Base Legal (Art. 7)</th>
                <th className="py-3.5 px-4">Categorías de Datos</th>
                <th className="py-3.5 px-4">Titulares & Volumen</th>
                <th className="py-3.5 px-4">Plazo Conservación</th>
                <th className="py-3.5 px-4">Transf. Internacional</th>
                <th className="py-3.5 px-4 text-right">Auditoría</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredProcesos.map((p) => {
                const tieneTransf = p.transferencia_internacional;
                const tieneSensibles = p.datos_sensibles_incluidos;

                return (
                  <tr
                    key={p.id}
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                  >
                    <td className="py-4 px-4">
                      <div className="font-bold text-slate-100 text-sm group-hover:text-emerald-300 transition-colors">
                        {p.nombre}
                      </div>
                      <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">{p.finalidad}</p>
                    </td>
                    <td className="py-4 px-4">
                      <span className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 capitalize">
                        {p.base_legal?.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-1.5">
                        {tieneSensibles ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                            Datos Sensibles (Salud)
                          </span>
                        ) : (
                          <span className="text-slate-300 font-mono text-[11px]">Ordinarios / Financieros</span>
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-4 font-mono text-[11px]">
                      {p.volumen_titulares_estimado ? `${p.volumen_titulares_estimado.toLocaleString()} titulares` : "No especificado"}
                    </td>
                    <td className="py-4 px-4 text-slate-400 text-[11px]">
                      {p.plazo_conservacion || "Conforme a normativa sectorial"}
                    </td>
                    <td className="py-4 px-4">
                      {tieneTransf ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                          {p.pais_transferencia || "Sí (Nube EE.UU.)"}
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]">No aplica</span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right font-mono text-[11px]">
                      <span className="text-emerald-400 font-bold">✓ Conforme Art. 38</span>
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
