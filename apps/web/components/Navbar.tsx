"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Shield,
  Search,
  Settings,
  Bell,
  Scale,
  Terminal,
  LogOut,
  Building2,
  CheckCircle2,
} from "lucide-react";
import { useProfile } from "./ProfileContext";
import { setAccessToken } from "@/lib/api";

const navLinks = [
  { name: "Dashboard", href: "/dashboard" },
  { name: "RAT Procesos", href: "/dashboard/procesos" },
  { name: "Matriz Riesgos", href: "/dashboard/riesgos" },
  { name: "Derechos LOPDP", href: "/dashboard/derechos" },
  { name: "Brechas SPDP", href: "/dashboard/brechas" },
  { name: "Casos & Auditoría", href: "/dashboard/casos" },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { mode, toggleMode } = useProfile();
  const [searchQuery, setSearchQuery] = useState("");

  const handleLogout = () => {
    setAccessToken(null);
    router.push("/login");
  };

  return (
    <header className="h-20 px-8 flex items-center justify-between bg-[#f8fafc] border-b border-slate-200/80 sticky top-0 z-40 backdrop-blur-md">
      {/* ── Left: Brand & Horizontal Nav ───────────────────────── */}
      <div className="flex items-center gap-10">
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-orange-600 to-amber-500 flex items-center justify-center shadow-md shadow-orange-500/20 group-hover:scale-105 transition-transform">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-extrabold text-slate-900 text-lg tracking-tight leading-none">
              OS PRIVACIDAD
            </div>
            <div className="text-[10px] font-bold text-orange-600 tracking-wider uppercase mt-0.5">
              ECUADOR 2026
            </div>
          </div>
        </Link>

        {/* Horizontal Navigation Tabs (as shown in reference design) */}
        <nav className="hidden lg:flex items-center gap-7 text-sm font-medium text-slate-600">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`relative py-2 transition-colors ${
                  isActive
                    ? "text-slate-950 font-bold"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                {link.name}
                {isActive && (
                  <span className="absolute bottom-0 left-0 w-full h-[2.5px] bg-slate-950 rounded-full" />
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* ── Right: Search, Persona Switcher & Controls ─────────── */}
      <div className="flex items-center gap-3">
        {/* Search Capsule Input */}
        <div className="relative hidden md:block w-64 xl:w-72">
          <input
            type="text"
            placeholder="Buscar procesos, brechas, titulares..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-4 pr-10 py-2.5 rounded-full bg-white border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all shadow-sm"
          />
          <Search className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2" />
        </div>

        {/* Persona Switcher Pill */}
        <button
          onClick={toggleMode}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold transition-all shadow-sm border ${
            mode === "juridico"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800 hover:bg-emerald-100"
              : "bg-sky-50 border-sky-200 text-sky-800 hover:bg-sky-100"
          }`}
          title="Alternar entre Modo Jurídico (DPO/Auditor) y Modo Técnico (CISO/TI)"
        >
          {mode === "juridico" ? (
            <>
              <Scale className="w-3.5 h-3.5 text-emerald-600" />
              <span>Modo DPO / Legal</span>
            </>
          ) : (
            <>
              <Terminal className="w-3.5 h-3.5 text-sky-600" />
              <span>Modo CISO / TI</span>
            </>
          )}
          <span className="text-[10px] opacity-60 font-mono">⇄</span>
        </button>

        {/* Settings Icon Pill */}
        <button className="w-10 h-10 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors shadow-sm">
          <Settings className="w-4 h-4" />
        </button>

        {/* Notification Bell with Dot */}
        <div className="relative">
          <button className="w-10 h-10 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors shadow-sm">
            <Bell className="w-4 h-4" />
          </button>
          <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-orange-500 ring-2 ring-white" />
        </div>

        {/* User Profile Avatar with Logout */}
        <div className="flex items-center gap-2 pl-2">
          <button
            onClick={handleLogout}
            className="w-10 h-10 rounded-full bg-gradient-to-tr from-slate-800 to-slate-700 text-white font-bold text-xs flex items-center justify-center shadow-md hover:ring-2 hover:ring-orange-500 transition-all"
            title="Cerrar sesión"
          >
            AD
          </button>
        </div>
      </div>
    </header>
  );
}
