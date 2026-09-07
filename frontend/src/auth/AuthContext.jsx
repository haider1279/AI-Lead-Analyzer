import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { supabase, isSupabaseConfigured } from './supabaseClient';
import { api } from '../services/api';

const AuthContext = createContext(null);

/**
 * Loads the user's authoritative profile from the database.
 * Priority 1: FastAPI /auth/me endpoint (queries public.profiles table).
 * Priority 2: Direct Supabase client query to public.profiles.
 * 
 * NEVER reads or trusts user_metadata.role.
 */
async function fetchAuthoritativeProfile(userId, token) {
  // 1. Try FastAPI backend (/auth/me)
  try {
    const profile = await api.auth.getMe();
    if (profile && profile.role) {
      return profile;
    }
  } catch (err) {
    console.warn('[Auth] /auth/me call failed, attempting direct Supabase profile query:', err.message);
  }

  // 2. Fallback: Query Supabase public.profiles directly using the authenticated client
  if (supabase && userId) {
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .single();

      if (!error && data && data.role) {
        return data;
      }
      if (error) {
        console.warn('[Auth] Direct Supabase profile query error:', error.message);
      }
    } catch (e) {
      console.warn('[Auth] Direct Supabase profile query exception:', e.message);
    }
  }

  return null;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const activeFetchRef = useRef(0);

  /**
   * Synchronizes session state and loads profile with authoritative role.
   */
  const syncUserFromSession = useCallback(async (currentSession) => {
    const fetchId = ++activeFetchRef.current;

    if (!currentSession?.user) {
      setSession(null);
      setUser(null);
      localStorage.removeItem('euroshub_auth_token');
      setLoading(false);
      return null;
    }

    // Immediately save access token so api.* calls are authenticated
    localStorage.setItem('euroshub_auth_token', currentSession.access_token);
    setSession(currentSession);

    // Fetch authoritative profile (reads public.profiles.role)
    const profile = await fetchAuthoritativeProfile(
      currentSession.user.id,
      currentSession.access_token
    );

    // If another auth change started while we were fetching, ignore stale result
    if (fetchId !== activeFetchRef.current) {
      return null;
    }

    const userData = {
      id: currentSession.user.id,
      email: currentSession.user.email,
      name:
        profile?.name ||
        currentSession.user.user_metadata?.name ||
        currentSession.user.email?.split('@')[0] ||
        'User',
      role: profile?.role ? profile.role.toLowerCase() : 'employee',
      avatar_url: profile?.avatar_url || null,
      created_at: profile?.created_at || null,
    };

    setUser(userData);
    setLoading(false);
    return userData;
  }, []);

  useEffect(() => {
    if (!isSupabaseConfigured || !supabase) {
      console.warn('[Auth] Supabase credentials missing in frontend environment.');
      setLoading(false);
      return;
    }

    // 1. Initial session check on mount
    supabase.auth.getSession().then(async ({ data: { session: initialSession }, error }) => {
      if (error) {
        console.error('[Auth] Error getting initial session:', error);
      }
      await syncUserFromSession(initialSession);
    });

    // 2. Listen for auth state changes (sign in, sign out, token refresh)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_event, newSession) => {
      await syncUserFromSession(newSession);
    });

    return () => subscription.unsubscribe();
  }, [syncUserFromSession]);

  const login = async (email, password) => {
    if (!isSupabaseConfigured || !supabase) {
      throw new Error('Supabase is not configured. Please verify frontend environment settings.');
    }
    if (!email || !email.trim()) {
      throw new Error('Email address is required.');
    }
    if (!password || !password.trim()) {
      throw new Error('Password is required.');
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    });

    if (error) {
      throw error;
    }

    if (data?.session) {
      // Synchronously load profile before returning so caller navigates with authoritative role
      await syncUserFromSession(data.session);
    }

    return data;
  };

  const signup = async (email, password, name) => {
    if (!isSupabaseConfigured || !supabase) {
      throw new Error('Supabase is not configured. Please verify frontend environment settings.');
    }
    if (!email || !email.trim()) {
      throw new Error('Email address is required.');
    }
    if (!password || !password.trim()) {
      throw new Error('Password is required.');
    }

    const { data, error } = await supabase.auth.signUp({
      email: email.trim(),
      password,
      options: {
        data: {
          name: name ? name.trim() : email.trim().split('@')[0],
        },
      },
    });

    if (error) {
      throw error;
    }

    if (data?.session) {
      await syncUserFromSession(data.session);
    }

    return data;
  };

  const logout = async () => {
    if (isSupabaseConfigured && supabase) {
      try {
        await supabase.auth.signOut();
      } catch (err) {
        console.error('[Auth] Error signing out of Supabase:', err);
      }
    }
    localStorage.removeItem('euroshub_auth_token');
    setSession(null);
    setUser(null);
  };

  // Authoritative admin check: role must strictly equal 'admin'
  const isAdmin = Boolean(user?.role && user.role.toLowerCase() === 'admin');

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role || 'employee',
        isAdmin,
        session,
        loading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
}
