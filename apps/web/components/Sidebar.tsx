"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileSpreadsheet,
  AlertTriangle,
  Users2,
  Flame,
  FolderLock,
  History,
  FileText,
  HelpCircle,
  Scale,
} from "lucide-react";
import { useProfile } from "./ProfileContext";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  badgeColor?: string;
  normativa: string;
}

const navItems: NavItem[] = [
  {
    label: "Dashboard Ejecutivo",
    href: "/dashboard",
    icon: LayoutDashboard,
    normativa: "Resumen Global",
  },
  {
    label: "Registro RAT (Procesos)",
    href: "/dashboard/procesos",
    icon: FileSpreadsheet,
    badge: "9 Campos",
    badgeColor: "bg-teal-500/10 text-teal-400 border-teal-500/20",
    normativa: "Art. 38 RGLOPDP",
  },
  {
    label: "Matriz Riesgos & EIPD",
    href: "/dashboard/riesgos",
    icon: AlertTriangle,
    badge: "R=P(I×V)",
    badgeColor: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    normativa: "Res. 2026-0005-R",
  },
  {
    label: "Catálogo de Derechos",
    href: "/dashboard/derechos",
    icon: Users2,
    badge: "15d SLA",
    badgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    normativa: "Cap. III LOPDP",
  },
  {
    label: "Brechas de Seguridad",
    href: "/dashboard/brechas",
    icon: Flame,
    badge: "5d SPDP",
    badgeColor: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    normativa: "Art. 43 LOPDP",
  },
  {
    label: "Casos & Expedientes",
    href: "/dashboard/casos",
    icon: FolderLock,
    badge: "Auditoría",
    badgeColor: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    normativa: "Máquina Estados",
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { mode } = useProfile();

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/60 backdrop-blur-md flex flex-col justify-between shrink-0 h-[calc(100vh-4rem)] sticky top-16">
      <div className="p-4 space-y-6">
        {/* Navigation list */}
        <div className="space-y-1">
          <div className="px-3 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Módulos LOPDP 2026
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all group ${
                  isActive
                    ? mode === "juridico"
                      ? "bg-emerald-600/15 text-emerald-300 border border-emerald-500/30 shadow-sm"
                      : "bg-sky-600/15 text-sky-300 border border-sky-500/30 shadow-sm"
                    : "text-slate-300 hover:text-slate-100 hover:bg-slate-900/80 border border-transparent"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`w-4 h-4 transition-colors ${
                      isActive
                        ? mode === "juridico"
                          ? "text-emerald-400"
                          : "text-sky-400"
                        : "text-slate-400 group-hover:text-slate-200"
                    }`}
                  />
                  <span>{item.label}</span>
                </div>

                {item.badge && (
                  <span
                    className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border ${
                      item.badgeColor || "bg-slate-800 text-slate-400 border-slate-700"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>

        {/* Normative Reference Widget */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold mb-1.5">
            <Scale className="w-4 h-4" />
            <span>Marco Legal Activo</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed mb-2">
            Registro Oficial Suplemento 459 & Guías Metodológicas SPDP 2026.
          </p>
          <div className="text-[10px] text-slate-400 font-mono flex items-center justify-between pt-2 border-t border-slate-800">
            <span>SLA Días Hábiles</span>
            <span className="text-emerald-400 font-bold">Activo</span>
          </div>
        </div>
      </div>

      {/* Footer / System Status */}
      <div className="p-4 border-t border-slate-900 text-[11px] text-slate-400 flex items-center justify-between">
        <span>v2.0 • LOPDP Ecuador</span>
        <span className="font-mono text-emerald-400">PostgreSQL RLS</span>
      </div>
    </aside>
  );
}
