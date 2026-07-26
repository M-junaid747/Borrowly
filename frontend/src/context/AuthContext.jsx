import React, { createContext, useContext, useEffect, useState } from "react";

import { api, clearTokens } from "../api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const hasToken = localStorage.getItem("access_token");
    if (!hasToken) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (username, password) => {
    await api.login(username, password);
    const me = await api.me();
    setUser(me);
    return me;
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  const switchRole = async (role) => {
    const updated = await api.switchRole(role);
    setUser(updated);
    return updated;
  };

  return (
    <AuthContext.Provider value={{ user, setUser, login, logout, switchRole, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
