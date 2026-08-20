import { create } from "zustand";

import { setAccessToken } from "@/lib/api";
import type { User } from "@/types";

type AuthState = {
  user: User | null;
  ready: boolean;
  setSession: (user: User, accessToken: string) => void;
  clearSession: () => void;
  setReady: (ready: boolean) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  ready: false,
  setSession: (user, accessToken) => {
    setAccessToken(accessToken);
    set({ user, ready: true });
  },
  clearSession: () => {
    setAccessToken(null);
    set({ user: null, ready: true });
  },
  setReady: (ready) => set({ ready }),
}));
