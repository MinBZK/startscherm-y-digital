'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import keycloak from '@/lib/keycloak';

interface KeycloakContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => void;
  logout: () => void;
}

const KeycloakContext = createContext<KeycloakContextType | null>(null);

export function KeycloakProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [syncingSession, setSyncingSession] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Guard to prevent double initialization if LoginGate also calls init
    if ((keycloak as any).__initPromise) {
      console.log('[auth] Reusing existing Keycloak init promise');
      (keycloak as any).__initPromise.then((auth: boolean) => {
        console.log('[auth] Existing init promise resolved. Authenticated:', auth);
        setIsAuthenticated(auth);
        setIsLoading(false);
      }).catch((error: any) => {
        console.error('Keycloak init (existing promise) failed:', error);
        setIsLoading(false);
      });
      return;
    }
    if ((keycloak as any).__initialized) {
      console.log('[auth] Keycloak already initialized');
      setIsAuthenticated(!!keycloak.authenticated);
      setIsLoading(false);
      return;
    }
    console.log('[auth] Starting fresh Keycloak initialization');
    const silentUrl = window.location.origin + '/silent-check-sso.html';
    console.log('[auth] Attempt Keycloak check-sso with silent iframe', silentUrl);
    (keycloak as any).__initPromise = keycloak
      .init({
        onLoad: 'check-sso',
        silentCheckSsoRedirectUri: silentUrl,
        pkceMethod: 'S256'
      })
      .then((auth) => {
        (keycloak as any).__initialized = true;
        console.log('[auth] Keycloak init (check-sso) complete. Authenticated:', auth);
        setIsAuthenticated(auth);
        setIsLoading(false);
        return auth;
      })
      .catch(async (error) => {
        // Detect invalid_redirect_uri and retry without silent check using login-required.
        const msg = (error && (error.message || String(error))) || '';
        console.warn('[auth] Keycloak check-sso failed, will evaluate fallback. Error:', msg);
        if (/invalid_redirect_uri/i.test(msg)) {
          console.warn('[auth] Falling back to login-required without silentCheckSsoRedirectUri');
          try {
            const auth = await keycloak.init({
              onLoad: 'login-required',
              pkceMethod: 'S256'
            });
            (keycloak as any).__initialized = true;
            setIsAuthenticated(auth);
            setIsLoading(false);
            return auth;
          } catch (e2) {
            console.error('[auth] Fallback Keycloak init failed:', e2);
            setIsLoading(false);
            throw e2;
          }
        } else {
          console.error('Keycloak initialization failed (no fallback):', error);
          setIsLoading(false);
          throw error;
        }
      });
  }, []);

  useEffect(() => {
    const run = async () => {
      if (!isAuthenticated || !keycloak.token || syncingSession) return;

      const tokenParsed: any = (keycloak as any).tokenParsed || {};
      const syncKey = `v1:${(keycloak.token || '').slice(0,16)}:${tokenParsed.exp || ''}`;

      if ((keycloak as any).__sessionSynced === syncKey) return;
      try {
        if (typeof window !== 'undefined') {
          const stored = window.localStorage.getItem('bsw_session_synced');
          if (stored === syncKey) {
            (keycloak as any).__sessionSynced = syncKey; // mirror into runtime
            return; // already synced for this token
          }
        }
      } catch {/* ignore storage errors */}

      console.log('[auth] Session sync starting. isAuthenticated:', isAuthenticated, 'token length:', keycloak.token.length, 'syncKey:', syncKey);
      setSyncingSession(true);
      try {
        const res = await fetch('/api/session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: keycloak.token }),
          credentials: 'same-origin'
        });
        if (!res.ok) {
          let detail: any = null;
            try { detail = await res.json(); } catch {}
          console.error('[auth] Failed to establish server session cookie', res.status, detail);
        } else {
          (keycloak as any).__sessionSynced = syncKey;
          try { if (typeof window !== 'undefined') window.localStorage.setItem('bsw_session_synced', syncKey); } catch {}
          console.log('[auth] Session cookie set; triggering server component refresh (no full reload)');
          router.refresh();
        }
      } catch (e) {
        console.error('[auth] Error syncing session cookie', e);
      } finally {
        setSyncingSession(false);
        console.log('[auth] Session sync finished');
      }
    };
    run();
  }, [isAuthenticated, syncingSession, router]);

  const login = () => {
    keycloak.login();
  };

  const logout = () => {
    keycloak.logout();
  };

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <KeycloakContext.Provider value={{ isAuthenticated, isLoading, login, logout }}>
      {children}
    </KeycloakContext.Provider>
  );
}

export function useKeycloak() {
  const context = useContext(KeycloakContext);
  if (!context) {
    throw new Error('useKeycloak must be used within KeycloakProvider');
  }
  return context;
}