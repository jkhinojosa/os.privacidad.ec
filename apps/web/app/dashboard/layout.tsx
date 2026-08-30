"use client";

import React from "react";
import { ProfileProvider } from "@/components/ProfileContext";
import { Navbar } from "@/components/Navbar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProfileProvider>
      <div className="min-h-screen bg-[#f1f5f9] text-slate-900 flex flex-col antialiased selection:bg-orange-500/20 selection:text-orange-900">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 space-y-8">
          {children}
        </main>
      </div>
    </ProfileProvider>
  );
}
