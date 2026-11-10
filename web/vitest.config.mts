import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: { alias: { "@": fileURLToPath(new URL(".", import.meta.url)) } },
  esbuild: { jsx: "automatic" },
  // Pacific time: the zone where CFBD's 05:00Z "time TBA" placeholder falls on the previous day.
  test: { env: { TZ: "America/Los_Angeles" } },
});
