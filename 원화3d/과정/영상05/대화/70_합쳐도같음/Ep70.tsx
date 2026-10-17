import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Circle } from "@remotion/rough-notation";

// 70 편 카드 — 값: 결과진단59_W2(0.697) · 결과판정58(0.695 · 판0 칸 0.697 · 통과선 0.707) · 부품별 이김 285 · 짐 220 · 틀 묶음 네 개
// 이징 · 연쇄는 Root.tsx 머리 주석(lottiefiles motion-design) 과 같은 값
const 먹 = "rgb(40,40,50)", 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(220,160,30)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);

type 막 = { 이름: string; 값: number; 색: string };
export const 비교70 = ({ rows, 선 }: { rows: 막[]; 선?: number }) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const lo = 0.5, hi = 0.75, x0 = 330, 폭 = 560, 자 = (v: number) => x0 + 폭 * (v - lo) / (hi - lo);
  const 도장 = spring({ frame: f - 70, fps, config: { stiffness: 300, damping: 14 } });
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      {rows.map((r, i) => {
        const s = 8 + i * 12, p = interpolate(f, [s, s + 30], [0, 1], { ...C, easing: 이징 }), 등 = interpolate(f, [s, s + 6], [0, 1], C), y = 170 + i * 170;
        return (
          <React.Fragment key={r.이름}>
            <div style={{ position: "absolute", left: 30, top: y, height: 100, display: "flex", alignItems: "center", fontSize: 40, color: 먹, opacity: 등, translate: `0px ${(1 - 등) * 20}px` }}>{r.이름}</div>
            <div style={{ position: "absolute", left: x0, top: y, width: (자(r.값) - x0) * p, height: 100, borderRadius: 14, background: r.색 }} />
            <div style={{ position: "absolute", left: x0 + (자(r.값) - x0) * p - 150, top: y, width: 140, height: 100, display: "flex", alignItems: "center", justifyContent: "flex-end", fontSize: 46, color: "white", opacity: 등, fontVariantNumeric: "tabular-nums" }}>{(lo + (r.값 - lo) * p).toFixed(3)}</div>
          </React.Fragment>
        );
      })}
      {선 !== undefined && <>
        <div style={{ position: "absolute", left: 자(선) - 3, top: 140, width: 0, height: 360, borderLeft: `6px dashed ${초}`, opacity: interpolate(f, [40, 50], [0, 1], C) }} />
        <div style={{ position: "absolute", left: 자(선) - 120, top: 510, width: 240, textAlign: "center", fontSize: 32, color: 초, opacity: interpolate(f, [40, 50], [0, 1], C) }}>통과선 {선.toFixed(3)}</div>
      </>}
      <div style={{ position: "absolute", left: 330, top: 530, fontSize: 64, color: 빨, border: `7px solid ${빨}`, borderRadius: 18, padding: "0 22px", rotate: "-8deg", opacity: Math.min(Math.max(도장, 0) * 2, 1), scale: `${interpolate(도장, [0, 1], [1.6, 1])}` }}>거의 같음</div>
    </AbsoluteFill>
  );
};
export const 크기70 = () => <비교70 rows={[{ 이름: "원래 모델", 값: 0.697, 색: 회 }, { 이름: "두 배 크기", 값: 0.698, 색: 금 }]} />;
export const 결과70 = () => <비교70 rows={[{ 이름: "원래 모델", 값: 0.697, 색: 회 }, { 이름: "세 장 합침", 값: 0.695, 색: 금 }]} />;

// 세 장 합침: 등각 정육면체 · 위 · 앞 · 옆 판이 날아와 면에 붙고 → 판이 옅어지며 속에 덩어리
const S = 230;
const P = (x: number, y: number, z: number) => [500 + S * 0.866 * (x - y), 390 + S * (0.5 * (x + y - 1) - (z - 0.5))];
const 판들 = [
  { 이름: "위", m: (u: number, v: number) => P(u, v, 1), 날: [0, -320], 시: 6 },
  { 이름: "앞", m: (u: number, v: number) => P(u, 1, 1 - v), 날: [-300, 170], 시: 16 },
  { 이름: "옆", m: (u: number, v: number) => P(1, 1 - u, 1 - v), 날: [300, 170], 시: 26 },
];
const L모양 = [[0.18, 0.18], [0.82, 0.18], [0.82, 0.46], [0.46, 0.46], [0.46, 0.82], [0.18, 0.82]];
const 다각 = (pts: number[][], dx = 0, dy = 0) => pts.map(([x, y]) => `${x + dx},${y + dy}`).join(" ");
export const 합침70 = () => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const 옅 = interpolate(f, [70, 90], [1, 0.25], C), 덩 = spring({ frame: f - 78, fps, config: { stiffness: 220, damping: 16 } });
  const b = (a: number, c: number) => [a, c];
  const 상자 = (q: number) => { const lo = 0.5 - 0.3 * q, hi = 0.5 + 0.3 * q, z1 = 0.5 + 0.3 * q, zt = 0.5 + 0.05 * q; return [
    { c: "rgb(120,200,140)", p: [P(lo, lo, z1), P(hi, lo, z1), P(hi, hi, z1), P(lo, hi, z1)] },
    { c: 초, p: [P(lo, hi, lo), P(hi, hi, lo), P(hi, hi, z1), P(lo, hi, z1)] },
    { c: "rgb(30,120,60)", p: [P(hi, lo, lo), P(hi, hi, lo), P(hi, hi, z1), P(hi, lo, z1)] },
  ].map((o) => ({ ...o, zt })); };
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      <svg width={1000} height={700}>
        {덩 > 0.01 && 상자(Math.min(덩, 1.05)).map((o, i) => <polygon key={i} points={다각(o.p)} fill={o.c} stroke={먹} strokeWidth={3} />)}
        {판들.map((d) => {
          const p = interpolate(f, [d.시, d.시 + 24], [0, 1], { ...C, easing: 이징 }), dx = d.날[0] * (1 - p), dy = d.날[1] * (1 - p);
          const 면 = [d.m(0, 0), d.m(1, 0), d.m(1, 1), d.m(0, 1)], 실 = L모양.map(([u, v]) => d.m(u, v)), 가 = d.m(0.5, 0.5);
          return (
            <g key={d.이름} opacity={Math.min(p * 3, 1)}>
              <polygon points={다각(면, dx, dy)} fill="rgb(235,235,240)" fillOpacity={0.9 * 옅} stroke={금} strokeWidth={5} />
              <polygon points={다각(실, dx, dy)} fill="none" stroke={먹} strokeWidth={5} strokeOpacity={옅} />
              <text x={가[0] + dx} y={가[1] + dy + 22} fontSize={64} fill={금} textAnchor="middle" stroke="white" strokeWidth={2} paintOrder="stroke">{d.이름}</text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

// 이김 · 짐: 712 를 가르는 띠 + 큰 숫자
export const 승패70 = () => {
  const f = useCurrentFrame();
  const p = interpolate(f, [8, 50], [0, 1], { ...C, easing: 이징 });
  const 칸 = [{ n: 285, 색: 초, 이름: "이김" }, { n: 207, 색: "rgb(200,200,206)", 이름: "비슷" }, { n: 220, 색: 빨, 이름: "짐" }];
  let x = 60;
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      <div style={{ position: "absolute", left: 60, top: 150, fontSize: 34, color: 회 }}>시험 부품 712 개 · 새 모델 기준</div>
      {칸.map((k) => { const w = 880 * k.n / 712 * p, l = x; x += 880 * k.n / 712; return <div key={k.이름} style={{ position: "absolute", left: l, top: 210, width: w, height: 80, background: k.색, borderRadius: 8 }} />; })}
      {[칸[0], 칸[2]].map((k, i) => (
        <div key={k.이름} style={{ position: "absolute", left: i ? 540 : 80, top: 340, width: 380, textAlign: "center", color: k.색, opacity: interpolate(f, [20, 30], [0, 1], C) }}>
          <div style={{ fontSize: 150, fontVariantNumeric: "tabular-nums", lineHeight: 1 }}>{Math.round(k.n * p)}</div>
          <div style={{ fontSize: 52 }}>{k.이름}</div>
        </div>
      ))}
    </AbsoluteFill>
  );
};

// 묶음 네 개(쉬움 → 어려움) · 회 = 원래 · 금 = 새 모델 · 어려운 묶음에 손그림 동그라미
const 묶음 = [{ 이름: "쉬움\n168", a: 0.931, b: 0.923 }, { 이름: "\n220", a: 0.845, b: 0.848 }, { 이름: "\n107", a: 0.692, b: 0.697 }, { 이름: "어려움\n217", a: 0.369, b: 0.363 }];
export const 어려움70 = () => {
  const f = useCurrentFrame();
  const 손 = interpolate(f, [62, 84], [0, 1], { ...C, easing: Easing.inOut(Easing.quad) }), 바닥 = 560, 높 = 400;
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      {묶음.map((g, i) => {
        const s = 6 + i * 6, p = interpolate(f, [s, s + 30], [0, 1], { ...C, easing: 이징 }), cx = 150 + i * 235;
        const 막대 = (v: number, dx: number, 색: string) => <div style={{ position: "absolute", left: cx + dx, top: 바닥 - 높 * v * p, width: 80, height: 높 * v * p, background: 색, borderRadius: "10px 10px 0 0" }} />;
        const 숫 = (v: number, dx: number, 색: string) => <div style={{ position: "absolute", left: cx + dx - 20, top: 바닥 - 높 * v * p - 50, width: 120, textAlign: "center", fontSize: 28, color: 색, opacity: p, fontVariantNumeric: "tabular-nums" }}>{(v * p).toFixed(3)}</div>;
        return (
          <React.Fragment key={i}>
            {막대(g.a, -84, 회)}{막대(g.b, 4, 금)}
            {i === 3 ? <div style={{ position: "absolute", left: cx - 104, top: 바닥 - 높 * g.a * p - 52, width: 208, height: 46 }}>
              <Circle progress={손} color={빨} strokeWidth={6} padding={18} seed={3 + Math.floor(f / 3)} roughness={1.6}><div style={{ width: 208, height: 46 }} /></Circle></div> : null}
            {숫(g.a, -84, 회)}{숫(g.b, 4, 금)}
            <div style={{ position: "absolute", left: cx - 110, top: 바닥 + 10, width: 220, textAlign: "center", fontSize: 34, color: i === 3 ? 빨 : 먹, whiteSpace: "pre-line", lineHeight: 1.15 }}>{g.이름}</div>
          </React.Fragment>
        );
      })}
      <div style={{ position: "absolute", left: 600, top: 110, fontSize: 32, color: 회 }}><span style={{ color: 회 }}>■ 원래</span>　<span style={{ color: 금 }}>■ 세 장 합침</span></div>
    </AbsoluteFill>
  );
};
