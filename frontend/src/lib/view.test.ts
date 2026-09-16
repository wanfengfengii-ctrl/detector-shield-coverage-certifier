import { describe, expect, it } from "vitest";
import { evidenceRectAttrs, polygonPoints, STATUS_TEXT } from "./view";

describe("polygonPoints", () => {
  it("将顶点数组转换为 SVG points 字符串", () => {
    expect(
      polygonPoints([
        [0, 0],
        [10, 0],
        [10, 5],
      ]),
    ).toBe("0,0 10,0 10,5");
  });

  it("空数组返回空字符串", () => {
    expect(polygonPoints([])).toBe("");
  });
});

describe("evidenceRectAttrs", () => {
  it("以左下角坐标计算 SVG rect 属性（输入坐标系，不经翻转）", () => {
    const attrs = evidenceRectAttrs({
      category: "gap",
      left: 3,
      bottom: 4,
      right: 8,
      top: 9,
    });
    expect(attrs).toEqual({ x: 3, y: 4, width: 5, height: 5 });
  });

  it("零面积接触矩形宽高为 0", () => {
    const attrs = evidenceRectAttrs({
      category: "overlap",
      left: 5,
      bottom: 5,
      right: 5,
      top: 7,
    });
    expect(attrs.width).toBe(0);
    expect(attrs.height).toBe(2);
  });
});

describe("STATUS_TEXT", () => {
  it("覆盖全部四种状态", () => {
    expect(Object.keys(STATUS_TEXT).sort()).toEqual(
      ["exact", "gap", "mixed", "overlap"].sort(),
    );
  });
});
