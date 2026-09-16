import { describe, expect, it, vi } from "vitest";
import { analyzeBoard } from "./api";
import { ApiValidationError } from "./types";

function mockResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("analyzeBoard", () => {
  it("成功时返回解析后的结果并按原文发送", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      mockResponse(200, {
        status: "exact",
        gapArea: 0,
        overlapArea: 0,
        evidence: [],
      }),
    );
    const raw = '{"width":1,"height":1,"polygons":[]}';
    const result = await analyzeBoard(raw, fetchMock);

    expect(result.status).toBe("exact");
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/analyze");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(raw);
  });

  it("422 时抛出携带聚合错误的 ApiValidationError", async () => {
    const errors = [
      { pointer: "/polygons/0/0", message: "存在斜边" },
      { pointer: "/width", message: "width 必须是整数" },
    ];
    const fetchMock = vi
      .fn()
      .mockImplementation(async () => mockResponse(422, { errors }));

    await expect(analyzeBoard("{}", fetchMock)).rejects.toBeInstanceOf(
      ApiValidationError,
    );
    const promise = analyzeBoard("{}", fetchMock);
    await expect(promise).rejects.toMatchObject({
      errors,
    });
  });

  it("422 响应缺少 errors 字段时给出空数组", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockResponse(422, {}));
    await expect(analyzeBoard("{}", fetchMock)).rejects.toMatchObject({
      errors: [],
    });
  });

  it("500 等其他状态抛出普通错误", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockResponse(500, {}));
    await expect(analyzeBoard("{}", fetchMock)).rejects.toThrow(
      "异常状态码 500",
    );
  });

  it("网络失败时抛出连接错误", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(analyzeBoard("{}", fetchMock)).rejects.toThrow(/无法连接/);
  });
});
