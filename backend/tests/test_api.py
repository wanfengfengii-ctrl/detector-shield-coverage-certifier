"""FastAPI 接口测试：状态码、错误聚合、JSON Pointer 排序。"""

import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def post(data):
    return client.post("/api/analyze", json=data)


def post_raw(text):
    return client.post(
        "/api/analyze", content=text, headers={"content-type": "application/json"}
    )


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200


def test_exact_tiling():
    r2 = post(
        {
            "width": 10,
            "height": 10,
            "polygons": [[[0, 0], [10, 0], [10, 10], [0, 10]]],
        }
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["status"] == "exact"
    assert body["gapArea"] == 0
    assert body["overlapArea"] == 0
    assert body["evidence"] == []


def test_missing_fields_aggregated_and_sorted():
    r = post({})
    assert r.status_code == 422
    errors = r.json()["errors"]
    pointers = [e["pointer"] for e in errors]
    assert pointers == sorted(pointers)  # JSON Pointer 码点序
    assert "/height" in pointers
    assert "/polygons" in pointers
    assert "/width" in pointers
    assert pointers.index("/height") < pointers.index("/polygons")
    assert pointers.index("/polygons") < pointers.index("/width")


def test_boundary_width_height():
    # 边界：0 与 10001 非法；1 与 10000 合法
    bad = post({"width": 0, "height": 1, "polygons": []})
    assert bad.status_code == 422
    assert any(e["pointer"] == "/width" for e in bad.json()["errors"])
    bad2 = post({"width": 10001, "height": 1, "polygons": []})
    assert bad2.status_code == 422
    ok = post({"width": 1, "height": 1, "polygons": []})
    assert ok.status_code == 200
    assert ok.json()["status"] == "gap"


def test_out_of_bounds_pointer():
    r = post(
        {
            "width": 10,
            "height": 10,
            "polygons": [[[0, 0], [11, 0], [11, 5], [0, 5]]],
        }
    )
    assert r.status_code == 422
    errors = r.json()["errors"]
    assert any(e["pointer"] == "/polygons/0/1/0" for e in errors)
    assert all(e["pointer"].startswith("/polygons/") for e in errors)


def test_zero_length_edge():
    r = post(
        {
            "width": 10,
            "height": 10,
            "polygons": [[[0, 0], [5, 0], [5, 0], [5, 5], [0, 5]]],
        }
    )
    assert r.status_code == 422
    assert any("零长度" in e["message"] for e in r.json()["errors"])


def test_diagonal_edge_rejected():
    r = post(
        {
            "width": 10,
            "height": 10,
            "polygons": [[[0, 0], [5, 3], [5, 5], [0, 5]]],
        }
    )
    assert r.status_code == 422
    assert any("斜边" in e["message"] for e in r.json()["errors"])
    assert any(e["pointer"] == "/polygons/0/0" for e in r.json()["errors"])


def test_repeated_first_point():
    r = post(
        {
            "width": 10,
            "height": 10,
            # 5 个点且末点重复首点
            "polygons": [[[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]]],
        }
    )
    assert r.status_code == 422
    assert any("隐式闭合" in e["message"] for e in r.json()["errors"])


def test_too_many_polygons():
    body = {"width": 10, "height": 10, "polygons": []}
    for _ in range(81):
        body["polygons"].append([[0, 0], [1, 0], [1, 1], [0, 1]])
    r = post(body)
    assert r.status_code == 422
    assert any("最多 80" in e["message"] for e in r.json()["errors"])


def test_vertex_count_limits():
    good = [[0, 0], [1, 0], [1, 1], [0, 1]]
    r = post({"width": 10, "height": 10, "polygons": [good[:3]]})
    assert r.status_code == 422
    big = []
    x = y = 0
    # 构造 121 个顶点的正交折线（简单性由调用方保证，此处只验数量）
    pts = []
    for i in range(121):
        pts.append([i % 2, (i * 2) % 3])
    r2 = post({"width": 10, "height": 10, "polygons": [pts]})
    assert r2.status_code == 422
    assert any("120" in e["message"] for e in r2.json()["errors"])


def test_bool_is_not_integer():
    r = post({"width": True, "height": 10, "polygons": []})
    assert r.status_code == 422
    assert any(e["pointer"] == "/width" for e in r.json()["errors"])


def test_float_coords_rejected():
    r = post(
        {
            "width": 10,
            "height": 10,
            "polygons": [[[0, 0], [5.5, 0], [5.5, 5], [0, 5]]],
        }
    )
    assert r.status_code == 422
    assert any(e["pointer"] == "/polygons/0/1/0" for e in r.json()["errors"])


def test_invalid_json_body():
    r = post_raw("{not json")
    assert r.status_code == 422
    assert r.json()["errors"][0]["pointer"] == ""


def test_empty_body():
    r = post_raw("")
    assert r.status_code == 422


def test_missing_width_still_reports_polygon_structure_errors():
    # 缺 width 时，拼片自身的结构/边错误仍必须聚合上报
    r = post(
        {
            "height": 10,
            "polygons": [
                [[0, 0], [5, 3], [5, 5], [0, 5]],   # 斜边
                [[1, 1], [2, 1], [2, 2]],            # 顶点数不足
                "not-a-polygon",
            ],
        }
    )
    assert r.status_code == 422
    pointers = {e["pointer"] for e in r.json()["errors"]}
    assert "/width" in pointers
    assert "/polygons/0/0" in pointers       # 斜边边指针
    assert "/polygons/1" in pointers         # 顶点数
    assert "/polygons/2" in pointers         # 非数组多边形


def test_diagonal_edge_reported_without_width_height():
    r = post({"polygons": [[[0, 0], [5, 3], [5, 5], [0, 5]]]})
    assert r.status_code == 422
    msgs = [e["message"] for e in r.json()["errors"]]
    assert any("斜边" in m for m in msgs)


def test_pointer_codepoint_order_with_nested_indices():
    r = post(
        {
            "width": 10,
            "height": 10,
            "polygons": [
                [[0, 0], [11, 0], [11, 5], [0, 5]],  # 越界
                "not-a-polygon",
            ],
        }
    )
    assert r.status_code == 422
    pointers = [e["pointer"] for e in r.json()["errors"]]
    assert pointers == sorted(pointers)
    assert "/polygons/0/1/0" in pointers
    assert "/polygons/1" in pointers


def test_response_shape_on_overlap():
    # 两矩形在 [8,12] 叠压且并集恰好铺满整板：有叠压无缺口
    r = post(
        {
            "width": 20,
            "height": 10,
            "polygons": [
                [[0, 0], [12, 0], [12, 10], [0, 10]],
                [[8, 0], [20, 0], [20, 10], [8, 10]],
            ],
        }
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "overlap"
    assert body["overlapArea"] == 40  # [8,12] x [0,10]
    assert body["gapArea"] == 0
    ev = body["evidence"]
    assert len(ev) == 1
    assert ev[0]["category"] == "overlap"
    assert (ev[0]["left"], ev[0]["bottom"], ev[0]["right"], ev[0]["top"]) == (
        8,
        0,
        12,
        10,
    )
