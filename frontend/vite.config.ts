/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 本地开发 / preview 时代理到后端；容器内由 nginx 代理
const apiProxy = {
  "/api": {
    target: process.env.VITE_API_TARGET ?? "http://localhost:8000",
    changeOrigin: true,
  },
};

export default defineConfig({
  plugins: [react()],
  server: { host: true, port: 5173, proxy: apiProxy },
  preview: { host: true, port: 4173, proxy: apiProxy },
  test: {
    // 单元测试只在 src 内；e2e/*.spec.ts 由 Playwright 运行
    include: ["src/**/*.{test,spec}.ts"],
  },
});
