import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": process.env.RULEREPLAY_API_TARGET ?? "http://127.0.0.1:8000",
    },
  },
  preview: {
    proxy: {
      "/api": process.env.RULEREPLAY_API_TARGET ?? "http://127.0.0.1:8000",
    },
  },
  test: {
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    environment: "jsdom",
    setupFiles: "./src/test-setup.ts",
  },
});
