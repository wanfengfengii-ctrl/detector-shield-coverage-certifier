"""条带扫描覆盖分析（纯整数运算，无几何布尔库、无浮点面积）。

输入已通过校验：顶点为整数、多边形为正交简单多边形且不越界。

思路
----
1. 以 ``0``、基板宽度 ``W`` 及所有顶点横坐标作为切分位置，得到竖条带
   ``[x0, x1]``；在开条带 ``(x0, x1)`` 内部，多边形边界的覆盖纵区间恒定。
2. 对每条开条带取一个整数代表 x，求每个多边形与该竖直线横交的水平边，
   交点纵坐标即水平边的整数 y；按奇偶配对得到该多边形的内部纵区间。
3. 用端点事件统计所有多边形的覆盖重数：0 = 缺口，1 = 正常，>=2 = 叠压。
4. 条带内合并同类且相邻的纵区间；仅当连续条带的类别与纵区间序列完全
   相同时才横向合并为证据矩形。面积均为整数宽×高之积。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

GAP = 0
COVERED = 1
OVERLAP = 2

CATEGORY_NAMES = {GAP: "gap", COVERED: "covered", OVERLAP: "overlap"}


@dataclass(frozen=True, slots=True)
class Evidence:
    """一条证据矩形（坐标轴方向，整数边界）。"""

    category: int
    left: int
    bottom: int
    right: int
    top: int

    def as_dict(self) -> dict[str, str | int]:
        return {
            "category": CATEGORY_NAMES[self.category],
            "left": self.left,
            "bottom": self.bottom,
            "right": self.right,
            "top": self.top,
        }


@dataclass(frozen=True, slots=True)
class Segment:
    """纵轴上的闭区间 [lo, hi]，端点为整数。"""

    lo: int
    hi: int


def _polygon_y_spans(
    points: list[tuple[int, int]], x: int
) -> list[Segment]:
    """多边形在开条带内代表横坐标 ``x`` 处覆盖的纵区间。

    正交多边形中只有水平边会与竖直线横交（竖直边与切分线平行，且开条带
    内部 x 不等于任何顶点横坐标），交点 y 为整数，按奇偶配对。

    条带宽度为 1 时开区间内没有严格内点，代表点取左边界 x0；此时采用
    左闭右开规则 ``lo <= x < hi``：计入从 x0 向右延伸的边、排除在 x0
    终止（属于左侧条带）的边。对严格内点代表该规则结果与严格包含相同。
    """
    ys: list[int] = []
    n = len(points)
    for i in range(n):
        ax, ay = points[i]
        bx, by = points[(i + 1) % n]
        if ay == by:  # 水平边
            lo_x, hi_x = (ax, bx) if ax < bx else (bx, ax)
            if lo_x <= x < hi_x:
                ys.append(ay)
        # 竖直边：与切分线平行，开条带内不与之横交
    ys.sort()
    return [Segment(ys[i], ys[i + 1]) for i in range(0, len(ys) - 1, 2)]


def _coverage_pieces(
    polygons: list[list[tuple[int, int]]], x: int, height: int
) -> list[tuple[int, Segment]]:
    """开条带 x 处的 (类别, 纵区间) 列表：GAP / COVERED / OVERLAP。"""
    coords: set[int] = {0, height}
    delta: dict[int, int] = defaultdict(int)
    for poly in polygons:
        for s in _polygon_y_spans(poly, x):
            coords.add(s.lo)
            coords.add(s.hi)
            delta[s.lo] += 1
            delta[s.hi] -= 1

    ordered = sorted(coords)
    raw: list[tuple[int, Segment]] = []
    depth = 0
    for y0, y1 in zip(ordered, ordered[1:]):
        depth += delta.get(y0, 0)
        if y1 == y0:
            continue
        if depth == 0:
            cat = GAP
        elif depth == 1:
            cat = COVERED
        else:
            cat = OVERLAP
        raw.append((cat, Segment(y0, y1)))

    # 合并同类且相邻的纵区间；异类相邻仅为零面积接触，不予合并
    merged: list[tuple[int, Segment]] = []
    for cat, s in raw:
        if merged and merged[-1][0] == cat and s.lo == merged[-1][1].hi:
            merged[-1] = (cat, Segment(merged[-1][1].lo, s.hi))
        else:
            merged.append((cat, s))
    return merged


def analyze(
    polygons: list[list[tuple[int, int]]], width: int, height: int
) -> dict[str, object]:
    """分析整板覆盖情况，返回状态、两类面积与证据矩形。"""
    cuts = {0, width}
    for poly in polygons:
        for px, _ in poly:
            cuts.add(px)
    xs = sorted(cuts)

    # (左边界, 右边界, 签名)；签名 = 条带内 (类别, 纵区间) 的完整序列
    columns: list[tuple[int, int, tuple[tuple[int, Segment], ...]]] = []
    for x0, x1 in zip(xs, xs[1:]):
        if x1 == x0:
            continue
        xm = x0 + (x1 - x0) // 2  # 开区间内的整数代表点
        pieces = _coverage_pieces(polygons, xm, height)
        columns.append((x0, x1, tuple(pieces)))

    evidence: list[Evidence] = []
    gap_area = 0
    overlap_area = 0

    def flush(
        x0: int,
        x1: int,
        signature: tuple[tuple[int, Segment], ...] | None,
    ) -> None:
        nonlocal gap_area, overlap_area
        if signature is None or x1 == x0:
            return
        for cat, s in signature:
            if cat == COVERED:
                continue  # 正常单层覆盖不出证据
            evidence.append(Evidence(cat, x0, s.lo, x1, s.hi))
            area = (x1 - x0) * (s.hi - s.lo)
            if cat == GAP:
                gap_area += area
            else:
                overlap_area += area

    # 横向合并：仅当连续条带的签名（类别 + 纵区间）完全相同
    group_x0 = group_x1 = 0
    group_sig: tuple[tuple[int, Segment], ...] | None = None
    for x0, x1, sig in columns:
        if sig == group_sig:
            group_x1 = x1
        else:
            flush(group_x0, group_x1, group_sig)
            group_x0, group_x1, group_sig = x0, x1, sig
    flush(group_x0, group_x1, group_sig)

    has_gap = any(e.category == GAP for e in evidence)
    has_overlap = any(e.category == OVERLAP for e in evidence)
    if has_gap and has_overlap:
        status = "mixed"
    elif has_gap:
        status = "gap"
    elif has_overlap:
        status = "overlap"
    else:
        status = "exact"

    # 证据按类别、左、下、右、上排序（gap 在 overlap 之前）
    evidence.sort(
        key=lambda e: (e.category, e.left, e.bottom, e.right, e.top)
    )
    return {
        "status": status,
        "gapArea": gap_area,
        "overlapArea": overlap_area,
        "evidence": [e.as_dict() for e in evidence],
    }
