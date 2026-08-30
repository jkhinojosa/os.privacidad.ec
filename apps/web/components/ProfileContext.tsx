"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export type UserProfileMode = "juridico" | "tecnico";

interface ProfileContextType {
  mode: UserProfileMode;
  setMode: (mode: UserProfileMode) => void;
  toggleMode: () => void;
}

const ProfileContext = createContext<ProfileContextType>({
  mode: "juridico",
  setMode: () => {},
  toggleMode: () => {},
});

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<UserProfileMode>("juridico");

  useEffect(() => {
    const saved = localStorage.getItem("os_profile_mode") as UserProfileMode;
    if (saved === "juridico" || saved === "tecnico") {
      setModeState(saved);
    }
  }, []);

  const setMode = (newMode: UserProfileMode) => {
    setModeState(newMode);
    localStorage.setItem("os_profile_mode", newMode);
  };

  const toggleMode = () => {
    setMode(mode === "juridico" ? "tecnico" : "juridico");
  };

  return (
    <ProfileContext.Provider value={{ mode, setMode, toggleMode }}>
      {children}
    </ProfileContext.Provider>
  );
}

export function useProfile() {
  return useContext(ProfileContext);
}
