"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Shield,
  Scale,
  Terminal,
  LogOut,
  Building2,
  Bell,
  CheckCircle2,
} from "lucide-react";
import { useProfile } from "./ProfileContext";
import { setAccessToken } from "@/lib/api";

export function Navbar() {
  const { mode, toggleMode } = useProfile();
  const router = useRouter();

  const handleLogout = () => {
    setAccessToken(null);
    router.push("/login");
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand & Organization */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-900/30 group-hover:scale-105 transition-transform">
            <Shield className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <div className="flex items-center gap-1.5 font-bold text-slate-100 text-base tracking-tight">
              <span>OS Privacidad</span>
              <span className="text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                EC 2026
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono">privacidad.ec</p>
          </div>
        </Link>

        <div className="h-5 w-px bg-slate-800 hidden sm:block" />

        {/* Tenant Selector Demo */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
          <Building2 className="w-3.5 h-3.5 text-emerald-400" />
          <span className="font-medium">FarmAndina Ecuador S.A.</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </div>
      </div>

      {/* Right Controls: Persona Switcher & User Menu */}
      <div className="flex items-center gap-3">
        {/* Persona Switcher Button */}
        <button
          onClick={toggleMode}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl border text-xs font-semibold transition-all shadow-sm ${
            mode === "juridico"
              ? "bg-emerald-950/50 border-emerald-700/60 text-emerald-300 hover:bg-emerald-900/60"
              : "bg-sky-950/50 border-sky-700/60 text-sky-300 hover:bg-sky-900/60"
          }`}
          title="Alternar entre Vista Jurídica (DPO/Auditor) y Vista Técnica (CISO/TI)"
        >
          {mode === "juridico" ? (
            <>
              <Scale className="w-3.5 h-3.5 text-emerald-400" />
              <span>Modo Jurídico (DPO / Auditor SPDP)</span>
            </>
          ) : (
            <>
              <Terminal className="w-3.5 h-3.5 text-sky-400" />
              <span>Modo Técnico (CISO / CRO / TI)</span>
            </>
          )}
          <span className="text-[10px] opacity-70 ml-1">⇄ Cambiar</span>
        </button>

        {/* Status indicator */}
        <div className="hidden md:flex items-center gap-1.5 text-[11px] text-emerald-400 font-mono bg-emerald-950/30 border border-emerald-800/30 px-2 py-1 rounded-lg">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>RLS Activo</span>
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
          title="Cerrar sesión"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
