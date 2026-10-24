import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// build: Django /static/ altından servis eder (STATICFILES_DIRS -> frontend/dist)
// dev:   Vite 5173'te çalışır, /api istekleri Django 8000'e proxy'lenir
export default defineConfig(({ command }) => ({
  plugins: [react(), tailwindcss()],
  base: command === "build" ? "/static/" : "/",
  server: {
    port: 5173,
    strictPort: true,
    proxy: { "/api": "http://localhost:8000" },
  },
}));
