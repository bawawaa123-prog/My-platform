import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

import {
  fetchCurrentUser,
  login as loginRequest,
  type LoginResponse,
  type UserRead,
} from "../api/auth";
import { registerUnauthorizedHandler, setAccessToken } from "../api/client";


const AUTH_STORAGE_KEY = "enterprise-support-agent.auth";

type AuthState = {
  accessToken: string | null;
  user: UserRead | null;
};

type AuthContextValue = {
  accessToken: string | null;
  user: UserRead | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  login: (payload: { email: string; password: string }) => Promise<LoginResponse>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredAuth(): AuthState {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) {
    return { accessToken: null, user: null };
  }

  try {
    const parsed = JSON.parse(raw) as AuthState;
    return {
      accessToken: parsed.accessToken ?? null,
      user: parsed.user ?? null,
    };
  } catch {
    return { accessToken: null, user: null };
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [state, setState] = useState<AuthState>(() => readStoredAuth());
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    setAccessToken(state.accessToken);
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  useEffect(() => {
    const handleUnauthorized = () => {
      setState({ accessToken: null, user: null });
    };

    registerUnauthorizedHandler(handleUnauthorized);
    return () => registerUnauthorizedHandler(null);
  }, []);

  useEffect(() => {
    let active = true;

    async function bootstrapAuth() {
      if (!state.accessToken) {
        setIsInitializing(false);
        return;
      }

      setAccessToken(state.accessToken);

      try {
        const user = await fetchCurrentUser();
        if (!active) {
          return;
        }
        setState((current) => ({
          ...current,
          user,
        }));
      } catch {
        if (!active) {
          return;
        }
        setState({ accessToken: null, user: null });
      } finally {
        if (active) {
          setIsInitializing(false);
        }
      }
    }

    void bootstrapAuth();

    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      accessToken: state.accessToken,
      user: state.user,
      isAuthenticated: Boolean(state.accessToken && state.user),
      isInitializing,
      async login(payload) {
        const result = await loginRequest(payload);
        setState({
          accessToken: result.access_token,
          user: result.user,
        });
        return result;
      },
      logout() {
        setState({ accessToken: null, user: null });
      },
    }),
    [isInitializing, state.accessToken, state.user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
