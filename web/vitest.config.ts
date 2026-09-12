import { defineConfig } from "vitest/config";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  test: { environment: "node", include: ["tests/**/*.test.ts"] },
  // `server-only` is a build-time boundary marker for the Next bundler. Under vitest there is
  // no client bundle to protect, so it resolves to nothing rather than throwing on import.
  resolve: { alias: { "@": root, "server-only": path.join(root, "tests/server-only-stub.ts") } },
});
