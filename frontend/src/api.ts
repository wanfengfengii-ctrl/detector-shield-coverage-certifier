import {
  ApiValidationError,
  type AnalyzeResponse,
  type ApiErrorItem,
} from "./types";

/**
 * 将基板 JSON 原文提交到分析 API。
 * 422（JSON 语法、结构、越界、零长度、斜边等聚合错误）抛出
 * ApiValidationError；其他网络或服务端错误抛出普通 Error。
 */
export async function analyzeBoard(
  rawJson: string,
  fetchImpl: typeof fetch = fetch,
): Promise<AnalyzeResponse> {
  let res: Response;
  try {
    res = await fetchImpl("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: rawJson,
    });
  } catch (err) {
    throw new Error(
      `无法连接分析服务：${err instanceof Error ? err.message : String(err)}`,
    );
  }

  if (res.status === 422) {
    const body = (await res.json()) as { errors?: ApiErrorItem[] };
    throw new ApiValidationError(Array.isArray(body.errors) ? body.errors : []);
  }
  if (!res.ok) {
    throw new Error(`服务返回异常状态码 ${res.status}`);
  }
  return (await res.json()) as AnalyzeResponse;
}
