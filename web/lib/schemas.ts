import { z } from "zod";

const symbolSchema = z.string().trim().min(4).max(5).transform((value) => value.toUpperCase());
const pillarSchema = z.enum(["concentration", "volume", "momentum", "catalyst"]);

export const profileSchema = z.object({
  id: z.enum(["flow-first", "catalyst-first"]),
  name: z.string().min(1).max(40),
  description: z.string(),
  watchlist: z.array(symbolSchema).min(1).max(60),
  owned: z.array(symbolSchema).max(60),
  config: z.object({
    horizon: z.enum(["event", "swing", "position"]),
    depth: z.enum(["compact", "standard", "forensic"]),
    pillarOrder: z.array(pillarSchema).length(4).refine((value) => new Set(value).size === 4, "Pillar order must contain four unique values"),
  }),
  // Sectors come from `company_report.overview.sector`, so the vocabulary is the payload's,
  // not this file's. Validating it against a hardcoded enum would reject real data.
  preferredSectors: z.array(z.string().min(1).max(60)),
  preferredEventTypes: z.array(z.enum(["company", "commodity", "rates", "currency", "policy", "weather"])),
  hasOnboarded: z.boolean(),
});

export const analyzeRequestSchema = z.object({ symbol: symbolSchema, profile: profileSchema });
export const impactRequestSchema = z.object({ eventId: z.string().min(1), profile: profileSchema, scope: z.enum(["watchlist", "market"]) });
export const userInsightSchema = z.object({
  id: z.string().min(1).max(100),
  symbol: symbolSchema,
  pillar: pillarSchema.optional(),
  category: z.enum(["data-error", "missing-context", "alternative-interpretation"]),
  note: z.string().trim().min(8).max(800),
  status: z.enum(["pending", "incorporated", "dismissed"]),
  createdAt: z.string().datetime(),
});

export const chatRequestSchema = z.object({
  question: z.string().trim().min(2).max(500),
  profile: profileSchema,
  contextSymbol: symbolSchema.optional(),
  userInsights: z.array(userInsightSchema).max(100).optional(),
});
