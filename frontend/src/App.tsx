import { useCallback, useRef, useState } from "react";
import { analyzeBoard } from "./api";
import BoardSvg, { type BoardData } from "./components/BoardSvg";
import { SAMPLE_JSON, STATUS_TEXT } from "./lib/view";
import {
  ApiValidationError,
  type AnalyzeRequest,
  type AnalyzeResponse,
} from "./types";

interface SuccessState {
  result: AnalyzeResponse;
  board: BoardData;
}

export default function App() {
  const [inputText, setInputText] = useState(SAMPLE_JSON);
  const [fileName, setFileName] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<SuccessState | null>(null);
  const [errors, setErrors] = useState<{ pointer: string; message: string }[]>(
    [],
  );
  const [fatal, setFatal] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // 提交时清除旧结果，但保留输入文本
  const handleSubmit = useCallback(async () => {
    setLoading(true);
    setSuccess(null);
    setErrors([]);
    setFatal(null);
    try {
      const result = await analyzeBoard(inputText);
      const parsed = JSON.parse(inputText) as AnalyzeRequest;
      setSuccess({ result, board: parsed as BoardData });
    } catch (err) {
      if (err instanceof ApiValidationError) {
        setErrors(err.errors);
      } else {
        setFatal(err instanceof Error ? err.message : String(err));
      }
    } finally {
      setLoading(false);
    }
  }, [inputText]);

  const handleFile = useCallback((file: File | undefined) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      setInputText(String(reader.result ?? ""));
      setFileName(file.name);
      // 载入新文件即清除旧结果
      setSuccess(null);
      setErrors([]);
      setFatal(null);
    };
    reader.onerror = () => setFatal(`文件读取失败：${file.name}`);
    reader.readAsText(file);
  }, []);

  const status = success?.result.status;

  return (
    <div className="app">
      <header className="app-header">
        <h1>高能射线探测器 · 屏蔽基板拼片质控</h1>
        <p className="subtitle">
          粘贴或上传基板 JSON，检测正交拼片的漏缝（缺口）与叠压；全部计算基于整数条带扫描。
        </p>
      </header>

      <main className="layout">
        <section className="panel input-panel" aria-label="基板 JSON 输入">
          <div className="panel-row">
            <label htmlFor="json-input" className="panel-title">
              基板 JSON
            </label>
            <div className="file-controls">
              <input
                ref={fileRef}
                id="file-upload"
                data-testid="file-upload"
                type="file"
                accept="application/json,.json"
                onChange={(e) => handleFile(e.target.files?.[0])}
                hidden
              />
              <button
                type="button"
                className="btn secondary"
                onClick={() => fileRef.current?.click()}
              >
                上传 JSON
              </button>
              {fileName && <span className="file-name" data-testid="file-name">{fileName}</span>}
            </div>
          </div>
          <textarea
            id="json-input"
            data-testid="json-input"
            className="json-input"
            spellCheck={false}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder='{"width": 10, "height": 10, "polygons": [[[0,0],[10,0],[10,10],[0,10]]]}'
          />
          <div className="panel-row">
            <button
              type="button"
              className="btn primary"
              data-testid="analyze-btn"
              disabled={loading}
              onClick={handleSubmit}
            >
              {loading ? "分析中…" : "分析覆盖"}
            </button>
            <button
              type="button"
              className="btn secondary"
              onClick={() => {
                setInputText("");
                setSuccess(null);
                setErrors([]);
                setFatal(null);
                setFileName(null);
                if (fileRef.current) fileRef.current.value = "";
              }}
            >
              清空
            </button>
          </div>
        </section>

        <section className="panel result-panel" aria-label="分析结果">
          {loading && <div className="notice" data-testid="loading">正在分析…</div>}

          {!loading && fatal && (
            <div className="notice fatal" data-testid="fatal-error" role="alert">
              {fatal}
            </div>
          )}

          {!loading && errors.length > 0 && (
            <div className="errors" data-testid="error-list">
              <h2 className="section-title">
                请求未通过校验（{errors.length} 个错误，HTTP 422）
              </h2>
              <ul className="error-list">
                {errors.map((e, i) => (
                  <li key={i} className="error-item" data-pointer={e.pointer}>
                    <code className="pointer">{e.pointer || "(根)"}</code>
                    <span>{e.message}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {!loading && !success && errors.length === 0 && !fatal && (
            <div className="notice" data-testid="empty-hint">
              提交后将在此显示覆盖状态、精确面积与证据。
            </div>
          )}

          {!loading && success && (
            <div className="result" data-testid="result">
              <div className="summary">
                <span className={`status-badge status-${status}`} data-testid="status-badge">
                  {STATUS_TEXT[status!]}
                </span>
                <span className="area" data-testid="gap-area">
                  缺口面积：<strong>{success.result.gapArea}</strong>
                </span>
                <span className="area" data-testid="overlap-area">
                  叠压面积：<strong>{success.result.overlapArea}</strong>
                </span>
                <span className="area">
                  证据矩形：<strong>{success.result.evidence.length}</strong> 个
                </span>
              </div>

              <h2 className="section-title">基板视图（纵轴已翻转叠绘）</h2>
              <div className="svg-wrap" data-testid="svg-wrap">
                <BoardSvg board={success.board} result={success.result} />
              </div>
              <ul className="legend">
                <li><span className="swatch tile-swatch" /> 拼片</li>
                <li><span className="swatch gap-swatch" /> 缺口证据</li>
                <li><span className="swatch overlap-swatch" /> 叠压证据</li>
              </ul>

              <h2 className="section-title">证据明细（按类别、左、下、右、上排序）</h2>
              {success.result.evidence.length === 0 ? (
                <p className="notice">无缺口或叠压证据。</p>
              ) : (
                <div className="table-wrap">
                  <table className="evidence-table" data-testid="evidence-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>类别</th>
                        <th>左 left</th>
                        <th>下 bottom</th>
                        <th>右 right</th>
                        <th>上 top</th>
                        <th>面积</th>
                      </tr>
                    </thead>
                    <tbody>
                      {success.result.evidence.map((e, i) => (
                        <tr key={i} data-category={e.category}>
                          <td>{i + 1}</td>
                          <td>{e.category === "gap" ? "缺口" : "叠压"}</td>
                          <td>{e.left}</td>
                          <td>{e.bottom}</td>
                          <td>{e.right}</td>
                          <td>{e.top}</td>
                          <td>{(e.right - e.left) * (e.top - e.bottom)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
