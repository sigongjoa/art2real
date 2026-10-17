import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// 71 편 카드 — 값: 결과판정60(어려운 217 0.363 → 0.437) · 조사61 A(반 칸 0.569 · 빈 정답 18) · 결과판정62(450/712 · 0.70 → 0.83 · 천장 0.90 · 거른 어려운 67 0.633 · 0.636)
const 먹 = "rgb(40,40,50)", 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(220,160,30)", 파 = "rgb(50,100,200)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);

type 막 = { 이름: string; 값: number; 색: string };
const 막대들 = ({ rows, lo, hi, 선, 선글, y0 = 170, 간 = 170 }: { rows: 막[]; lo: number; hi: number; 선?: number; 선글?: string; y0?: number; 간?: number }) => {
  const f = useCurrentFrame(); const x0 = 330, 폭 = 560, 자 = (v: number) => x0 + 폭 * (v - lo) / (hi - lo);
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      {rows.map((r, i) => {
        const s = 8 + i * 14, p = interpolate(f, [s, s + 30], [0, 1], { ...C, easing: 이징 }), 등 = interpolate(f, [s, s + 6], [0, 1], C), y = y0 + i * 간;
        return (
          <React.Fragment key={r.이름}>
            <div style={{ position: "absolute", left: 30, top: y, height: 100, display: "flex", alignItems: "center", fontSize: 38, color: 먹, opacity: 등, whiteSpace: "pre-line", lineHeight: 1.1 }}>{r.이름}</div>
            <div style={{ position: "absolute", left: x0, top: y, width: (자(r.값) - x0) * p, height: 100, borderRadius: 14, background: r.색 }} />
            <div style={{ position: "absolute", left: x0 + (자(r.값) - x0) * p - 150, top: y, width: 140, height: 100, display: "flex", alignItems: "center", justifyContent: "flex-end", fontSize: 46, color: "white", opacity: 등, fontVariantNumeric: "tabular-nums" }}>{(lo + (r.값 - lo) * p).toFixed(2)}</div>
          </React.Fragment>
        );
      })}
      {선 !== undefined && <>
        <div style={{ position: "absolute", left: 자(선) - 3, top: y0 - 30, height: rows.length * 간 + 20, borderLeft: `6px dashed ${파}`, opacity: interpolate(f, [50, 60], [0, 1], C) }} />
        <div style={{ position: "absolute", left: 자(선) - 200, top: y0 + rows.length * 간 - 4, width: 400, textAlign: "center", fontSize: 34, color: 파, opacity: interpolate(f, [50, 60], [0, 1], C) }}>{선글}</div>
      </>}
    </AbsoluteFill>
  );
};
export const 올라감71 = () => <막대들 rows={[{ 이름: "전부 배움", 값: 0.363, 색: 회 }, { 이름: "어려운 것만", 값: 0.437, 색: 초 }]} lo={0} hi={0.6} />;
export const 다시71 = () => <막대들 rows={[{ 이름: "712 개 전부", 값: 0.70, 색: 회 }, { 이름: "남은 450 개", 값: 0.83, 색: 초 }]} lo={0.5} hi={0.95} 선={0.9} 선글="이 채점의 최고 0.90" />;
export const 이득71 = () => <막대들 rows={[{ 이름: "어려운 217\n전부 배움", 값: 0.363, 색: 회 }, { 이름: "어려운 것만", 값: 0.437, 색: 초 }, { 이름: "남은 67\n전부 배움", 값: 0.633, 색: 회 }, { 이름: "어려운 것만", 값: 0.636, 색: 금 }]} lo={0} hi={0.8} y0={120} 간={125} />;

// 칸 격자 위 얇은 벽(두 칸) · 같은 모양이 반 칸 밀림 → 겹침이 줄어듦
const 칸 = 64, 열 = 12, 행 = 6, gx = 116, gy = 150;
const 격자 = () => <>{Array.from({ length: (열 + 1) }).map((_, i) => <div key={"v" + i} style={{ position: "absolute", left: gx + i * 칸, top: gy, width: 2, height: 행 * 칸, background: "rgb(215,215,222)" }} />)}
  {Array.from({ length: (행 + 1) }).map((_, i) => <div key={"h" + i} style={{ position: "absolute", left: gx, top: gy + i * 칸, width: 열 * 칸, height: 2, background: "rgb(215,215,222)" }} />)}</>;
export const 반칸71 = () => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const 밀 = interpolate(f, [40, 75], [0, 0.5], { ...C, easing: 이징 }), 숫 = spring({ frame: f - 80, fps, config: { stiffness: 260, damping: 16 } });
  const 벽 = (dx: number, 색: string, 테: boolean) => <div style={{ position: "absolute", left: gx + (5 + dx) * 칸, top: gy, width: 2 * 칸, height: 행 * 칸, background: 테 ? "transparent" : 색, border: 테 ? `8px solid ${색}` : "none", boxSizing: "border-box", opacity: 테 ? interpolate(f, [10, 25], [0, 1], C) : 1 }} />;
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      {격자()}{벽(0, "rgba(40,160,80,0.55)", false)}{벽(밀, 금, true)}
      <div style={{ position: "absolute", left: gx, top: gy + 행 * 칸 + 14, width: 열 * 칸, display: "flex", justifyContent: "space-between", fontSize: 34 }}>
        <span style={{ color: 초 }}>■ 정답 (벽 두 칸)</span><span style={{ color: 금 }}>□ 완벽한 답, 반 칸 밀림</span>
      </div>
      <div style={{ position: "absolute", left: 620, top: 40, fontSize: 70, color: 빨, opacity: Math.min(Math.max(숫, 0) * 2, 1), scale: `${interpolate(숫, [0, 1], [1.5, 1])}` }}>0.57</div>
      <div style={{ position: "absolute", left: 140, top: 62, fontSize: 34, color: 회, opacity: interpolate(f, [80, 90], [0, 1], C) }}>어려운 217 개 평균 →</div>
    </AbsoluteFill>
  );
};
// 칸 중심 점 · 칸보다 얇은 판 → 점이 하나도 안 들어감 → 칸 0 개
export const 빈칸71 = () => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const 판 = interpolate(f, [8, 30], [0, 1], { ...C, easing: 이징 }), 점 = interpolate(f, [30, 60], [0, 1], C), 숫 = spring({ frame: f - 72, fps, config: { stiffness: 260, damping: 16 } });
  const py = gy + 2.62 * 칸;
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      {격자()}
      {Array.from({ length: 열 * 행 }).map((_, k) => { const i = k % 열, j = Math.floor(k / 열), on = (i + j * 열) / (열 * 행) < 점; return <div key={k} style={{ position: "absolute", left: gx + (i + 0.5) * 칸 - 6, top: gy + (j + 0.5) * 칸 - 6, width: 12, height: 12, borderRadius: 6, background: 회, opacity: on ? 1 : 0 }} />; })}
      <div style={{ position: "absolute", left: gx + 칸 * 1.2, top: py, width: 칸 * 9.6 * 판, height: 14, background: 금, borderRadius: 4 }} />
      <div style={{ position: "absolute", left: gx, top: gy + 행 * 칸 + 14, width: 열 * 칸, display: "flex", justifyContent: "space-between", fontSize: 32 }}>
        <span style={{ color: 금 }}>━ 칸보다 얇은 판</span><span style={{ color: 회 }}>● 칸 가운데 점</span>
      </div>
      <div style={{ position: "absolute", left: 120, top: 44, fontSize: 52, color: 빨, opacity: Math.min(Math.max(숫, 0) * 2, 1), scale: `${interpolate(숫, [0, 1], [1.4, 1])}` }}>정답 칸 0 개 · 이런 부품 18 개</div>
    </AbsoluteFill>
  );
};
// 712 점 → 262 빨강으로 빠지고 450 남음
export const 거름71 = () => {
  const f = useCurrentFrame(); const 빠 = interpolate(f, [30, 70], [0, 1], { ...C, easing: 이징 }), 셈 = Math.round(712 - 262 * 빠);
  const 순 = (k: number) => ((k * 7919) % 712) / 712;   // 섞은 차례 — 빠지는 점이 고르게 흩어지게
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      {Array.from({ length: 712 }).map((_, k) => { const i = k % 32, j = Math.floor(k / 32), 나감 = 순(k) < 262 / 712, a = 나감 ? 빠 : 0;
        return <div key={k} style={{ position: "absolute", left: 92 + i * 26, top: 150 + j * 19, width: 16, height: 14, borderRadius: 4, background: 나감 && a > 0.3 ? 빨 : 초, opacity: 1 - 0.75 * a, translate: `0px ${a * 10}px` }} />; })}
      <div style={{ position: "absolute", left: 0, top: 40, width: 1000, textAlign: "center", fontSize: 72, color: 초, fontVariantNumeric: "tabular-nums" }}>{셈} 개 남음</div>
      <div style={{ position: "absolute", left: 0, top: 600, width: 1000, textAlign: "center", fontSize: 32, color: 빨, opacity: 빠 }}>빠짐: 너무 작음 · 너무 얇음(반 칸에 무너짐) · 부스러짐</div>
    </AbsoluteFill>
  );
};
