"""几何引擎单元测试。"""

from app.geometry import analyze


def test_exact_full_single_rectangle():
    polys = [[(0, 0), (10, 0), (10, 10), (0, 10)]]
    r = analyze(polys, 10, 10)
    assert r["status"] == "exact"
    assert r["gapArea"] == 0
    assert r["overlapArea"] == 0
    assert r["evidence"] == []


def test_exact_edge_contact_is_zero_area():
    # 两个矩形沿 x=5 边相接：零面积接触，不计叠压
    polys = [
        [(0, 0), (5, 0), (5, 10), (0, 10)],
        [(5, 0), (10, 0), (10, 10), (5, 10)],
    ]
    r = analyze(polys, 10, 10)
    assert r["status"] == "exact"
    assert r["evidence"] == []


def test_gap_areas_and_horizontal_merge():
    # 10x10 板中央 6x6 拼片
    polys = [[(2, 2), (8, 2), (8, 8), (2, 8)]]
    r = analyze(polys, 10, 10)
    assert r["status"] == "gap"
    assert r["gapArea"] == 64
    assert r["overlapArea"] == 0
    cats = {(e["left"], e["bottom"], e["right"], e["top"]) for e in r["evidence"]}
    assert cats == {(0, 0, 2, 10), (2, 0, 8, 2), (2, 8, 8, 10), (8, 0, 10, 10)}
    assert all(e["category"] == "gap" for e in r["evidence"])


def test_overlap_two_rectangles():
    polys = [
        [(0, 0), (6, 0), (6, 10), (0, 10)],
        [(4, 0), (10, 0), (10, 10), (4, 10)],
    ]
    r = analyze(polys, 10, 10)
    assert r["status"] == "overlap"
    assert r["overlapArea"] == 20  # [4,6] x [0,10]
    assert r["gapArea"] == 0
    assert len(r["evidence"]) == 1
    e = r["evidence"][0]
    assert (e["left"], e["bottom"], e["right"], e["top"]) == (4, 0, 6, 10)


def test_mixed_gap_and_overlap():
    # 两块各 6 宽，在 [4,6] 叠压；板右侧 [6,10] 有缺口（第二块结束于 10？）
    polys = [
        [(0, 0), (6, 0), (6, 6), (0, 6)],
        [(4, 4), (10, 4), (10, 10), (4, 10)],
    ]
    r = analyze(polys, 10, 10)
    assert r["status"] == "mixed"
    # 叠压：[4,6]x[4,6] = 4
    assert r["overlapArea"] == 4
    # 缺口：板 100 - 并集 (36+36-4=68) = 32
    assert r["gapArea"] == 32


def test_l_shaped_polygon_exact_board():
    # L 形拼片恰好铺满 10x10 的一部分，其余为缺口
    l_poly = [(0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)]
    r = analyze([l_poly], 10, 10)
    # L 面积 = 10*4 + 4*6 = 64，缺口 36
    assert r["gapArea"] == 36
    assert r["status"] == "gap"


def test_t_shaped_internal_cut():
    # T 形凹多边形，顶点横坐标会切出多条带
    t_poly = [(2, 0), (8, 0), (8, 4), (6, 4), (6, 10), (4, 10), (4, 4), (2, 4)]
    r = analyze([t_poly], 10, 10)
    # T 面积 = 6*4 + 2*6 = 36
    assert r["gapArea"] == 64
    assert r["overlapArea"] == 0


def test_evidence_sorted_category_then_coords():
    polys = [
        # 叠压区 + 缺口同时存在
        [(0, 0), (6, 0), (6, 6), (0, 6)],
        [(4, 4), (8, 4), (8, 8), (4, 8)],
    ]
    r = analyze(polys, 10, 10)
    ev = r["evidence"]
    keys = [
        (
            0 if e["category"] == "gap" else 1,
            e["left"],
            e["bottom"],
            e["right"],
            e["top"],
        )
        for e in ev
    ]
    assert keys == sorted(keys)


def test_integer_area_no_floats():
    polys = [[(1, 1), (9, 1), (9, 9), (1, 9)]]
    r = analyze(polys, 10, 10)
    assert isinstance(r["gapArea"], int)
    assert isinstance(r["overlapArea"], int)
    assert r["gapArea"] == 36


def test_strip_signature_identical_across_multiple_cuts_merges():
    # 顶点横坐标落在另一拼片内部但不改变签名时，应横向合并
    polys = [
        [(0, 0), (10, 0), (10, 5), (0, 5)],  # 下半板
        [(3, 5), (7, 5), (7, 10), (3, 10)],  # 上半板中间 4 宽
    ]
    r = analyze(polys, 10, 10)
    # 缺口：上半板两侧 3*5 * 2 = 30
    assert r["gapArea"] == 30
    # 上半条带 [0,3] 与 [7,10] 签名相同（整高缺口）但不连续，不合并
    gap_rects = [e for e in r["evidence"] if e["category"] == "gap"]
    assert (0, 5, 3, 10) in {(e["left"], e["bottom"], e["right"], e["top"]) for e in gap_rects}
    assert (7, 5, 10, 10) in {(e["left"], e["bottom"], e["right"], e["top"]) for e in gap_rects}


def test_point_contact_only_no_overlap():
    # 两矩形仅在一点 (5,5) 相触
    polys = [
        [(0, 0), (5, 0), (5, 5), (0, 5)],
        [(5, 5), (10, 5), (10, 10), (5, 10)],
    ]
    r = analyze(polys, 10, 10)
    assert r["overlapArea"] == 0
    # 两矩形面积和 50，其余皆缺口
    assert r["gapArea"] == 50


def test_interlocking_staircase_exact():
    # 两个正交多边形以阶梯缝咬合，恰好铺满 8x8（含内顶点横坐标切条带）
    a = [(0, 0), (4, 0), (4, 2), (6, 2), (6, 4), (8, 4), (8, 8), (0, 8)]
    b = [(4, 0), (8, 0), (8, 4), (6, 4), (6, 2), (4, 2)]
    r = analyze([a, b], 8, 8)
    assert r["status"] == "exact"
    assert r["evidence"] == []


def test_triple_overlap_depths():
    # 三块满高矩形在 14x10 板上依次错叠 2 个单位
    polys = [
        [(0, 0), (10, 0), (10, 10), (0, 10)],
        [(2, 0), (12, 0), (12, 10), (2, 10)],
        [(4, 0), (14, 0), (14, 10), (4, 10)],
    ]
    r = analyze(polys, 14, 10)
    assert r["status"] == "overlap"
    assert r["gapArea"] == 0
    # 连续条带签名相同（均为 overlap × [0,10]），横向合并为一个证据矩形；
    # 重数 2 与重数 3 同属“至少 2”，总面积 = 20 + 60 + 20 = 100
    assert r["overlapArea"] == 100
    overlaps = [e for e in r["evidence"] if e["category"] == "overlap"]
    assert len(overlaps) == 1
    e = overlaps[0]
    assert (e["left"], e["bottom"], e["right"], e["top"]) == (2, 0, 12, 10)


def test_zero_area_line_contact_between_overlap_and_gap_ignored():
    # 叠压矩形与下方缺口仅在 y=5 线段相触：不产生额外证据，面积精确
    polys = [
        [(0, 5), (10, 5), (10, 10), (0, 10)],  # 整条上半板
        [(0, 5), (5, 5), (5, 10), (0, 10)],    # 左上 1/4，在 [0,5]x[5,10] 叠压
    ]
    r = analyze(polys, 10, 10)
    assert r["status"] == "mixed"
    assert r["overlapArea"] == 25
    assert r["gapArea"] == 50  # 下半板整宽


def test_unit_width_open_strips():
    # 所有条带宽度均为 1（整数 x=0..4）：开区间内无严格内点
    polys = [
        [(0, 0), (1, 0), (1, 2), (0, 2)],
        [(1, 0), (2, 0), (2, 2), (1, 2)],
        [(2, 0), (3, 0), (3, 2), (2, 2)],
    ]
    r = analyze(polys, 4, 2)
    assert r["status"] == "gap"
    assert r["gapArea"] == 2  # 仅 [3,4] x [0,2]
    assert r["overlapArea"] == 0
    gaps = {(e["left"], e["right"], e["bottom"], e["top"]) for e in r["evidence"]}
    assert gaps == {(3, 4, 0, 2)}


def test_minimal_one_by_one_board():
    r = analyze([[(0, 0), (1, 0), (1, 1), (0, 1)]], 1, 1)
    assert r["status"] == "exact"
    assert r["evidence"] == []


def test_unit_width_overlap_strip():
    # 两个 1 单位宽拼片占据同一个单位宽条带
    polys = [
        [(0, 0), (1, 0), (1, 2), (0, 2)],
        [(0, 0), (1, 0), (1, 2), (0, 2)],
    ]
    r = analyze(polys, 2, 2)
    # [0,1] 两片重叠（面积 2），[1,2] 缺口（面积 2）
    assert r["status"] == "mixed"
    assert r["overlapArea"] == 2
    assert r["gapArea"] == 2
