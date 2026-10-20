// 학습 그림 115 의 모델 — 부품 59(컵) 위 방향 원 안 영역의 실제 코드 후보(코드110 시험: 껍질 0 · A2 15 · A0 31 · 관통 32) · 원화 차트 = 정답 층 16
// 학습 = 비교기가 후보 넷을 다 다시 그려 원화와 맞대고, 가장 덜 어긋난 후보를 정답으로 · 고르기 확률(소프트맥스)을 교차 엔트로피 기울기로 그쪽으로 당김
export const LAYERS = 32;
export const CANDS = [{ name: "껍질", L: 0 }, { name: "선 A2", L: 15 }, { name: "선 A0", L: 31 }, { name: "관통", L: 32 }];
export const TRUTH = 16;
export const CUP = { h: 34, outer: 8, inner: 5 };   // 카드 · 스크린에 그리는 컵 단면(세계 단위)
export const depthOf = (L) => CUP.h * Math.min(L, LAYERS) / LAYERS;   // 윗면에서 바닥까지
export function mismatch(L) {   // 다시 그린 단면과 원화 단면이 어긋난 넓이 / 단면 넓이
  const area = 2 * CUP.outer * CUP.h - 2 * CUP.inner * depthOf(TRUTH);
  return (2 * CUP.inner * Math.abs(depthOf(L) - depthOf(TRUTH))) / area;
}
export const softmax = (w) => { const m = Math.max(...w); const e = w.map((x) => Math.exp(x - m)); const s = e.reduce((a, b) => a + b, 0); return e.map((x) => x / s); };
export const LR = 1.1;
export function train(epochs) {   // → 회차마다 { p(학습 전), 재기[4], 정답 번호, p(학습 뒤) }
  let w = CANDS.map(() => 0); const out = [];
  for (let e = 0; e < epochs; e++) {
    const p = softmax(w); const reads = CANDS.map((c) => mismatch(c.L)); const best = reads.indexOf(Math.min(...reads));
    w = w.map((x, i) => x + LR * ((i === best ? 1 : 0) - p[i])); out.push({ p, reads, best, after: softmax(w) });
  }
  return out;
}
if (import.meta.url === `file://${process.argv[1]?.replace(/\\/g, "/")}` || process.argv[1]?.endsWith("model.mjs")) {   // 자가 검사
  const r = train(6), m = CANDS.map((c) => mismatch(c.L));
  console.assert(m.indexOf(Math.min(...m)) === 1, "정답 후보는 층 15");
  console.assert(Math.abs(r[0].p[1] - 0.25) < 1e-9 && r[5].after[1] > 0.8, "확률이 정답 쪽으로 오른다");
  console.log("어긋남", m.map((x) => (100 * x).toFixed(1) + "%").join(" "), "· 정답 쪽 확률", r.map((x) => x.after[1].toFixed(2)).join(" "));
}
