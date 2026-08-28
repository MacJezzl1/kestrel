'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, UserProfile, AuthResponse } from '@/lib/api';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  rememberMe: boolean;
  setRememberMe: (val: boolean) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  updateToken: (newToken: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Storage helpers — pick localStorage (persist) or sessionStorage (session only)
function getStorage(remember: boolean): Storage {
  return remember ? localStorage : sessionStorage;
}

function getRememberPref(): boolean {
  if (typeof window === 'undefined') return true;
  return localStorage.getItem('kestrel_remember') !== 'false';
}

function findToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('kestrel_token') || sessionStorage.getItem('kestrel_token') || null;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [rememberMe, setRememberMeState] = useState(true);

  const setRememberMe = useCallback((val: boolean) => {
    setRememberMeState(val);
    localStorage.setItem('kestrel_remember', val ? 'true' : 'false');
  }, []);

  // Save token to appropriate storage
  const saveToken = useCallback((t: string) => {
    const storage = getStorage(rememberMe);
    storage.setItem('kestrel_token', t);
    setToken(t);
  }, [rememberMe]);

  // Load saved session on mount
  useEffect(() => {
    const remember = getRememberPref();
    setRememberMeState(remember);

    const savedToken = findToken();
    if (savedToken) {
      setToken(savedToken);
      api.getProfile()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem('kestrel_token');
          sessionStorage.removeItem('kestrel_token');
          setToken(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response: AuthResponse = await api.login(email, password);
    const storage = getStorage(getRememberPref());
    storage.setItem('kestrel_token', response.access_token);
    setToken(response.access_token);
    setUser(response.user);
  }, []);

  const register = useCallback(async (email: string, password: string, fullName?: string) => {
    const response: AuthResponse = await api.register(email, password, fullName);
    const storage = getStorage(getRememberPref());
    storage.setItem('kestrel_token', response.access_token);
    setToken(response.access_token);
    setUser(response.user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('kestrel_token');
    sessionStorage.removeItem('kestrel_token');
    setToken(null);
    setUser(null);
  }, []);

  const updateToken = useCallback((newToken: string) => {
    const storage = getStorage(getRememberPref());
    // Clear both, then write to correct one
    localStorage.removeItem('kestrel_token');
    sessionStorage.removeItem('kestrel_token');
    storage.setItem('kestrel_token', newToken);
    setToken(newToken);
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      token,
      isLoading,
      isAuthenticated: !!user && !!token,
      rememberMe,
      setRememberMe,
      login,
      register,
      logout,
      updateToken,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
