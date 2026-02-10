import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { api, clearTokens, ApiError } from '../api/client';
import type { UserResponse, TokenResponse, LoginRequest, RegisterRequest } from '../types';

interface AuthState {
  user: UserResponse | null;
  loading: boolean;
  isLoggedIn: boolean;
  isAdmin: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const u = await api<UserResponse>('/auth/me');
      setUser(u);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (data: LoginRequest) => {
    const tokens = await api<TokenResponse>('/auth/login', {
      method: 'POST',
      body: data,
      auth: false,
    });
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    await fetchUser();
  };

  const register = async (data: RegisterRequest) => {
    await api<UserResponse>('/auth/register', {
      method: 'POST',
      body: data,
      auth: false,
    });
  };

  const logout = async () => {
    const rt = localStorage.getItem('refresh_token');
    if (rt) {
      try {
        await api('/auth/logout', {
          method: 'POST',
          body: { refresh_token: rt },
        });
      } catch (err) {
        if (!(err instanceof ApiError)) throw err;
      }
    }
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isLoggedIn: !!user,
        isAdmin: user?.role === 'admin',
        login,
        register,
        logout,
        refreshUser: fetchUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
