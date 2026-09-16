import type { AnalyzeResponse } from "../types";
import { evidenceRectAttrs, polygonPoints } from "../lib/view";

export interface BoardData {
  width: number;
  height: number;
  polygons: number[][][];
}

interface BoardSvgProps {
  board: BoardData;
  result: AnalyzeResponse;
}

/**
 * 以基板宽高作为 viewBox，通过 translate + scale(1,-1) 固定翻转纵轴，
 * 使输入坐标（y 向上）与 SVG 屏幕坐标（y 向下）一致叠绘。
 * 翻转组内不放文字，避免镜像。
 */
export default function BoardSvg({ board, result }: BoardSvgProps) {
  const { width, height, polygons } = board;
  const flip = `translate(0 ${height}) scale(1 -1)`;

  return (
    <svg
      className="board-svg"
      data-testid="board-svg"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label={`基板覆盖图，宽 ${width} 高 ${height}`}
    >
      <rect x={0} y={0} width={width} height={height} className="board-bg" />

      <g transform={flip}>
        {polygons.map((poly, i) => (
          <polygon
            key={`poly-${i}`}
            points={polygonPoints(poly)}
            className="tile"
            data-index={i}
          />
        ))}

        {result.evidence.map((e, i) => {
          const r = evidenceRectAttrs(e);
          return (
            <rect
              key={`ev-${i}`}
              {...r}
              className={`evidence evidence-${e.category}`}
              data-category={e.category}
            />
          );
        })}

        <rect
          x={0}
          y={0}
          width={width}
          height={height}
          className="board-outline"
          fill="none"
        />
      </g>
    </svg>
  );
}
