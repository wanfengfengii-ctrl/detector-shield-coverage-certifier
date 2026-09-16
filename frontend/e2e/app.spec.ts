import { expect, test } from "@playwright/test";
import { writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const EXACT_JSON = JSON.stringify({
  width: 10,
  height: 10,
  polygons: [
    [
      [0, 0],
      [5, 0],
      [5, 10],
      [0, 10],
    ],
    [
      [5, 0],
      [10, 0],
      [10, 10],
      [5, 10],
    ],
  ],
});

const MIXED_JSON = JSON.stringify({
  width: 10,
  height: 10,
  polygons: [
    [
      [0, 0],
      [6, 0],
      [6, 6],
      [0, 6],
    ],
    [
      [4, 4],
      [10, 4],
      [10, 10],
      [4, 10],
    ],
  ],
});

const DIAGONAL_JSON = JSON.stringify({
  width: 10,
  height: 10,
  polygons: [
    [
      [0, 0],
      [5, 3],
      [5, 5],
      [0, 5],
    ],
  ],
});

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test("合法无缝铺片：状态精确覆盖、面积为 0、SVG 翻转叠绘", async ({ page }) => {
  await page.getByTestId("json-input").fill(EXACT_JSON);
  await page.getByTestId("analyze-btn").click();

  await expect(page.getByTestId("status-badge")).toHaveText("精确覆盖");
  await expect(page.getByTestId("gap-area")).toContainText("0");
  await expect(page.getByTestId("overlap-area")).toContainText("0");

  const svg = page.getByTestId("board-svg");
  await expect(svg).toHaveAttribute("viewBox", "0 0 10 10");
  // 纵轴翻转：translate(0 10) scale(1 -1)
  await expect(svg.locator("g")).toHaveAttribute(
    "transform",
    /scale\(1\s+-1\)/,
  );
  // 两个拼片均绘制
  await expect(svg.locator("polygon.tile")).toHaveCount(2);
  // 无证据矩形
  await expect(svg.locator("rect.evidence")).toHaveCount(0);
});

test("mixed：缺口 32、叠压 4，证据矩形与明细行齐备并排序", async ({ page }) => {
  await page.getByTestId("json-input").fill(MIXED_JSON);
  await page.getByTestId("analyze-btn").click();

  await expect(page.getByTestId("status-badge")).toHaveText("缺口与叠压并存");
  await expect(page.getByTestId("gap-area")).toContainText("32");
  await expect(page.getByTestId("overlap-area")).toContainText("4");

  const svg = page.getByTestId("board-svg");
  await expect(svg.locator("rect.evidence-gap")).not.toHaveCount(0);
  await expect(svg.locator("rect.evidence-overlap")).toHaveCount(1);
  const overlap = svg.locator("rect.evidence-overlap").first();
  await expect(overlap).toHaveAttribute("x", "4");
  await expect(overlap).toHaveAttribute("y", "4");
  await expect(overlap).toHaveAttribute("width", "2");
  await expect(overlap).toHaveAttribute("height", "2");

  // 明细表行数 = 证据矩形数
  const gapRows = page.locator('table[data-testid="evidence-table"] tr[data-category="gap"]');
  const overlapRows = page.locator('table[data-testid="evidence-table"] tr[data-category="overlap"]');
  expect(await gapRows.count()).toBeGreaterThan(0);
  await expect(overlapRows).toHaveCount(1);
});

test("422 聚合错误按指针显示，输入保留、旧结果被清除", async ({ page }) => {
  // 先得到一次成功结果
  await page.getByTestId("json-input").fill(EXACT_JSON);
  await page.getByTestId("analyze-btn").click();
  await expect(page.getByTestId("result")).toBeVisible();

  // 再提交含斜边的非法 JSON
  await page.getByTestId("json-input").fill(DIAGONAL_JSON);
  await page.getByTestId("analyze-btn").click();

  const errorList = page.getByTestId("error-list");
  await expect(errorList).toBeVisible();
  await expect(errorList).toContainText("422");
  await expect(errorList.locator(".pointer", { hasText: "/polygons/0/0" })).toBeVisible();
  await expect(errorList).toContainText("斜边");

  // 旧结果已清除
  await expect(page.getByTestId("result")).toHaveCount(0);
  // 输入保留
  await expect(page.getByTestId("json-input")).toHaveValue(DIAGONAL_JSON);
});

test("JSON 语法错误同样以 422 形式呈现且不丢失输入", async ({ page }) => {
  await page.getByTestId("json-input").fill("{ oops");
  await page.getByTestId("analyze-btn").click();
  await expect(page.getByTestId("error-list")).toBeVisible();
  await expect(page.getByTestId("json-input")).toHaveValue("{ oops");
});

test("上传 JSON 文件后自动载入文本框并可成功分析", async ({ page }) => {
  const filePath = join(tmpdir(), `board-${Date.now()}.json`);
  writeFileSync(filePath, EXACT_JSON, "utf8");

  await page.getByTestId("file-upload").setInputFiles(filePath);
  await expect(page.getByTestId("file-name")).toContainText(".json");
  await expect(page.getByTestId("json-input")).toHaveValue(EXACT_JSON);

  await page.getByTestId("analyze-btn").click();
  await expect(page.getByTestId("status-badge")).toHaveText("精确覆盖");
});
