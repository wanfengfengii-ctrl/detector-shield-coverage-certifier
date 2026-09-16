"""请求结构与语义校验：所有错误聚合并按 JSON Pointer 码点序排列。"""

from __future__ import annotations

from dataclasses import dataclass

MAX_POLYGONS = 80
MIN_VERTICES = 4
MAX_VERTICES = 120
MIN_COORD = 1
MAX_SIDE = 10_000


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    pointer: str
    message: str


def _is_int(value: object) -> bool:
    """JSON 整数（bool 在 Python 中是 int 子类，须排除）。"""
    return isinstance(value, int) and not isinstance(value, bool)


def _escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _ptr(*parts: object) -> str:
    if not parts:
        return ""
    return "/" + "/".join(_escape(str(p)) for p in parts)


def validate_document(data: object) -> list[ValidationIssue]:
    """对已解析的 JSON 文档做结构 + 语义校验，返回全部问题。"""
    issues: list[ValidationIssue] = []

    if not isinstance(data, dict):
        return [ValidationIssue("", "请求体必须是 JSON 对象")]

    width = data.get("width")
    height = data.get("height")

    for name, value in (("width", width), ("height", height)):
        pointer = _ptr(name)
        if not _is_int(value):
            kind = "缺失" if name not in data else "必须是整数"
            issues.append(ValidationIssue(pointer, f"{name} {kind}"))
        elif not (MIN_COORD <= value <= MAX_SIDE):
            issues.append(
                ValidationIssue(
                    pointer,
                    f"{name} 必须是 {MIN_COORD} 至 {MAX_SIDE} 之间的整数",
                )
            )

    polygons = data.get("polygons")
    if "polygons" not in data:
        issues.append(ValidationIssue(_ptr("polygons"), "polygons 缺失"))
        polygons = None
    elif not isinstance(polygons, list):
        issues.append(
            ValidationIssue(_ptr("polygons"), "polygons 必须是数组")
        )
        polygons = None
    elif len(polygons) > MAX_POLYGONS:
        issues.append(
            ValidationIssue(
                _ptr("polygons"),
                f"多边形数量最多 {MAX_POLYGONS} 个，当前 {len(polygons)} 个",
            )
        )

    if polygons is not None:
        for i, poly in enumerate(polygons):
            if not isinstance(poly, list):
                issues.append(
                    ValidationIssue(_ptr("polygons", i), "多边形必须是顶点数组")
                )
                continue
            if not (MIN_VERTICES <= len(poly) <= MAX_VERTICES):
                issues.append(
                    ValidationIssue(
                        _ptr("polygons", i),
                        f"多边形顶点数必须在 {MIN_VERTICES} 至 "
                        f"{MAX_VERTICES} 之间，当前 {len(poly)} 个",
                    )
                )

            points: list[tuple[int, int]] = []
            points_valid = True
            for j, point in enumerate(poly):
                if not isinstance(point, list) or len(point) != 2:
                    issues.append(
                        ValidationIssue(
                            _ptr("polygons", i, j),
                            "顶点必须是包含两个整数的数组 [x, y]",
                        )
                    )
                    points_valid = False
                    continue
                ok_xy = True
                xy: list[int] = []
                for axis, coord in zip((0, 1), point):
                    if not _is_int(coord):
                        issues.append(
                            ValidationIssue(
                                _ptr("polygons", i, j, axis),
                                "坐标必须是整数",
                            )
                        )
                        ok_xy = False
                    else:
                        xy.append(coord)
                if ok_xy:
                    points.append((xy[0], xy[1]))
                else:
                    points_valid = False

            if not points_valid or len(points) != len(poly):
                # 顶点存在结构问题时，跳过一切依赖完整坐标的检查；
                # 但其他多边形的检查继续（错误聚合）
                continue

            # 越界：x 只依赖宽度、y 只依赖高度，单边尺寸有效即检查对应坐标
            if _is_int(width) or _is_int(height):
                for j, (x, y) in enumerate(points):
                    if _is_int(width) and not (0 <= x <= width):
                        issues.append(
                            ValidationIssue(
                                _ptr("polygons", i, j, 0),
                                f"x 坐标 {x} 越界，允许范围 [0, {width}]",
                            )
                        )
                    if _is_int(height) and not (0 <= y <= height):
                        issues.append(
                            ValidationIssue(
                                _ptr("polygons", i, j, 1),
                                f"y 坐标 {y} 越界，允许范围 [0, {height}]",
                            )
                        )

            n = len(points)
            # 序列隐式闭合：首点不得在末尾重复（不依赖基板尺寸）
            if n >= 1 and points[0] == points[-1]:
                issues.append(
                    ValidationIssue(
                        _ptr("polygons", i, n - 1),
                        "序列隐式闭合，最后一个顶点不得与首点重复",
                    )
                )

            # 边：零长度 / 斜边（只依赖整数坐标，闭合边也检查）
            for j in range(n):
                ax, ay = points[j]
                bx, by = points[(j + 1) % n]
                if j == n - 1 and points[0] == points[-1]:
                    continue
                dx, dy = bx - ax, by - ay
                edge_pointer = _ptr("polygons", i, j)
                if dx == 0 and dy == 0:
                    issues.append(
                        ValidationIssue(edge_pointer, "存在零长度边")
                    )
                elif dx != 0 and dy != 0:
                    issues.append(
                        ValidationIssue(
                            edge_pointer,
                            "存在斜边，正交多边形的边必须水平或竖直",
                        )
                    )

    return issues


def sort_issues(issues: list[ValidationIssue]) -> list[ValidationIssue]:
    """按 JSON Pointer 的 Unicode 码点序（指针相同则按消息）。"""
    return sorted(issues, key=lambda e: (e.pointer, e.message))
