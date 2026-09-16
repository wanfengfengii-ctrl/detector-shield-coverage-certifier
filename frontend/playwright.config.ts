import { defineConfig, devices } from "@playwright/test";

// verify 容器内 web/api 已由 compose 启动，通过 BASE_URL 指向 Web 服务；
// 本地运行时先启动 backend(uvicorn) 与 frontend(vite preview)，
// 再设置 BASE_URL=http://localhost:4173。
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:4173",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
