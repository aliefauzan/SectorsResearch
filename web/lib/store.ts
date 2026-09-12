"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { demoProfiles } from "@/lib/profiles";
import type {
  AnswerDepth,
  FeedbackEvent,
  Horizon,
  LearnedPreference,
  PillarKey,
  SymbolCode,
  UserInsight,
  UserProfile,
} from "@/lib/types";

interface CatalystState {
  profile: UserProfile;
  preferences: LearnedPreference[];
  feedback: FeedbackEvent[];
  insights: UserInsight[];
  copilotOpen: boolean;
  setDemoProfile: (id: UserProfile["id"]) => void;
  setWatchlist: (symbols: SymbolCode[]) => void;
  toggleOwned: (symbol: SymbolCode) => void;
  setHorizon: (horizon: Horizon) => void;
  setDepth: (depth: AnswerDepth) => void;
  setPillarOrder: (order: PillarKey[]) => void;
  completeOnboarding: () => void;
  setCopilotOpen: (open: boolean) => void;
  recordFeedback: (input: Omit<FeedbackEvent, "id" | "createdAt">) => void;
  recordInsight: (input: Omit<UserInsight, "id" | "createdAt" | "status">) => void;
  setInsightStatus: (id: string, status: UserInsight["status"]) => void;
  removeInsight: (id: string) => void;
  togglePreference: (id: string) => void;
  resetMemory: () => void;
}

const basePreferences: LearnedPreference[] = [
  { id: "pref-order", label: "Mulai dari Konsentrasi", explanation: "Dipilih langsung saat setup.", source: "explicit", active: true },
  { id: "pref-depth", label: "Kedalaman standar", explanation: "Dipilih langsung saat setup.", source: "explicit", active: true },
];

export const useCatalystStore = create<CatalystState>()(
  persist(
    (set) => ({
      profile: structuredClone(demoProfiles[0]),
      preferences: basePreferences,
      feedback: [],
      insights: [],
      copilotOpen: false,
      setDemoProfile: (id) => set({ profile: structuredClone(demoProfiles.find((profile) => profile.id === id) ?? demoProfiles[0]) }),
      setWatchlist: (symbols) => set((state) => ({ profile: { ...state.profile, watchlist: symbols, owned: state.profile.owned.filter((symbol) => symbols.includes(symbol)) } })),
      toggleOwned: (symbol) => set((state) => ({
        profile: {
          ...state.profile,
          owned: state.profile.owned.includes(symbol)
            ? state.profile.owned.filter((item) => item !== symbol)
            : [...state.profile.owned, symbol],
        },
      })),
      setHorizon: (horizon) => set((state) => ({ profile: { ...state.profile, config: { ...state.profile.config, horizon } } })),
      setDepth: (depth) => set((state) => ({ profile: { ...state.profile, config: { ...state.profile.config, depth } } })),
      setPillarOrder: (pillarOrder) => set((state) => ({ profile: { ...state.profile, config: { ...state.profile.config, pillarOrder } } })),
      completeOnboarding: () => set((state) => ({ profile: { ...state.profile, hasOnboarded: true } })),
      setCopilotOpen: (copilotOpen) => set({ copilotOpen }),
      recordFeedback: (input) => set((state) => {
        const feedback: FeedbackEvent = { ...input, id: `fb-${Date.now()}`, createdAt: new Date().toISOString() };
        const label = input.action === "show-more" ? "Tampilkan analisis lebih dalam" : input.action === "useful" ? "Sumber ini berguna" : "Kurangi prioritas kasus serupa";
        const learned: LearnedPreference = { id: `learned-${feedback.id}`, label, explanation: "Dipelajari dari feedback yang dapat dibatalkan.", source: "feedback", active: true };
        return { feedback: [feedback, ...state.feedback], preferences: [learned, ...state.preferences] };
      }),
      recordInsight: (input) => set((state) => {
        const insight: UserInsight = { ...input, id: `insight-${Date.now()}`, status: "pending", createdAt: new Date().toISOString() };
        const learned: LearnedPreference = {
          id: `learned-${insight.id}`,
          label: `Verifikasi ulang ${insight.symbol}${insight.pillar ? ` · ${insight.pillar}` : ""}`,
          explanation: "Catatan user disimpan sebagai hipotesis terbuka sampai diverifikasi terhadap sumber.",
          source: "feedback",
          active: true,
        };
        return { insights: [insight, ...state.insights], preferences: [learned, ...state.preferences] };
      }),
      setInsightStatus: (id, status) => set((state) => ({ insights: state.insights.map((item) => item.id === id ? { ...item, status } : item) })),
      removeInsight: (id) => set((state) => ({ insights: state.insights.filter((item) => item.id !== id), preferences: state.preferences.filter((item) => item.id !== `learned-${id}`) })),
      togglePreference: (id) => set((state) => ({ preferences: state.preferences.map((item) => item.id === id ? { ...item, active: !item.active } : item) })),
      resetMemory: () => set({ preferences: basePreferences, feedback: [], insights: [] }),
    }),
    // v2 drops the fixture watchlist that v1 persisted: the symbols a deployment serves
    // come from the API, so a list saved against a different source is not restorable.
    { name: "catalyst:v2", version: 2 },
  ),
);
