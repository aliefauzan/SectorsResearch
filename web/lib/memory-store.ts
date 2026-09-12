"use client";

import { demoProfiles } from "@/lib/profiles";
import { useCatalystStore } from "@/lib/store";
import type { FeedbackEvent, MemoryStore, UserInsight } from "@/lib/types";

export const browserMemoryStore: MemoryStore = {
  loadProfile: () => useCatalystStore.getState().profile,
  recordFeedback: (feedback: FeedbackEvent) => useCatalystStore.getState().recordFeedback({ symbol: feedback.symbol, eventId: feedback.eventId, action: feedback.action }),
  recordInsight: (insight: UserInsight) => useCatalystStore.getState().recordInsight({ symbol: insight.symbol, pillar: insight.pillar, category: insight.category, note: insight.note }),
  listInsights: () => useCatalystStore.getState().insights,
  listPreferences: () => useCatalystStore.getState().preferences,
  compareProfiles: () => demoProfiles,
  reset: () => useCatalystStore.getState().resetMemory(),
};
