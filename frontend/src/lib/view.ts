import type { EvidenceRect } from "../types";

/** 将多边形顶点数组转为 SVG polygon 的 points 字符串。 */
export function polygonPoints(points: readonly (readonly number[])[]): string {
  return points.map((p) => `${p[0]},${p[1]}`).join(" ");
}

/** SVG <rect> 属性（坐标已是左下角坐标系）。 */
export function evidenceRectAttrs(e: EvidenceRect): {
  x: number;
  y: number;
  width: number;
  height: number;
} {
  return {
    x: e.left,
    y: e.bottom,
    width: e.right - e.left,
    height: e.top - e.bottom,
  };
}

export const STATUS_TEXT: Record<string, string> = {
  exact: "精确覆盖",
  gap: "存在缺口",
  overlap: "存在叠压",
  mixed: "缺口与叠压并存",
};

export const SAMPLE_JSON = `{
  "width": 20,
  "height": 10,
  "polygons": [
    [[0, 0], [12, 0], [12, 10], [0, 10]],
    [[8, 0], [18, 0], [18, 10], [8, 10]]
  ]
}`;
