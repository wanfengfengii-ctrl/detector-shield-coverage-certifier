export type BoardStatus = "exact" | "gap" | "overlap" | "mixed";
export type EvidenceCategory = "gap" | "overlap";

export interface AnalyzeRequest {
  width: number;
  height: number;
  polygons: number[][][];
}

export interface EvidenceRect {
  category: EvidenceCategory;
  left: number;
  bottom: number;
  right: number;
  top: number;
}

export interface AnalyzeResponse {
  status: BoardStatus;
  gapArea: number;
  overlapArea: number;
  evidence: EvidenceRect[];
}

export interface ApiErrorItem {
  pointer: string;
  message: string;
}

export class ApiValidationError extends Error {
  readonly errors: ApiErrorItem[];
  constructor(errors: ApiErrorItem[]) {
    super(`校验失败：${errors.length} 个错误`);
    this.name = "ApiValidationError";
    this.errors = errors;
  }
}
