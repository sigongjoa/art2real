import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Circle } from "@remotion/rough-notation";

// 72 편 카드 — 값: 결과판정62(58 칸 IoU 0.695) · 결과판정63(58 F 0.837) · 재료72 값.json(톱니링 0.80/1.00 · 모터판 0.95/0.97 · 관 0.46/0.21)
const 먹 = "rgb(40,40,50)", 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(220,160,30)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);

// 새 자: 정답 표면(초록 곡선) · 1 칸 띠 · 답 점이 띠 안이면 초록 · 밖이면 빨강
export const 자72 = () => {
  const f = useCurrentFrame();
  const 띠 = interpolate(f, [10, 30], [0, 1], { ...C, easing: 이징 }), y = (x: number) => 360 + 90 * Math.sin(x / 120);
  const 점 = Array.from({ length: 22 }).map((_, i) => { const x = 110 + i * 37, d = [10, -25, 30, -8, 55, 18, -40, 4, -70, 22, -12, 35, -5, 80, -28, 14, -50, 9, 26, -18, 62, -3][i]; return { x, yy: y(x) + d, 안: Math.abs(d) <= 45, s: 40 + i * 2 }; });
  const 맞 = 점.filter((p) => p.안 && f > p.s + 6).length;
  const 길 = Array.from({ length: 90 }).map((_, i) => { const x = 90 + i * 9.4; return `${x},${y(x)}`; }).join(" ");
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      <svg width={1000} height={700}>
        <polyline points={길} fill="none" stroke="rgba(40,160,80,0.18)" strokeWidth={90 * 띠} strokeLinecap="round" />
        <polyline points={길} fill="none" stroke={초} strokeWidth={8} />
        {점.map((p, i) => { const o = interpolate(f, [p.s, p.s + 6], [0, 1], C); return <circle key={i} cx={p.x} cy={p.yy} r={13} fill={f > p.s + 6 ? (p.안 ? 초 : 빨) : 금} stroke="white" strokeWidth={3} opacity={o} />; })}
      </svg>
      <div style={{ position: "absolute", left: 60, top: 110, fontSize: 36, color: 초, opacity: 띠 }}>━ 정답 표면 · 옅은 띠 = 1 칸 안</div>
      <div style={{ position: "absolute", left: 60, top: 560, fontSize: 52, color: 먹, opacity: interpolate(f, [40, 50], [0, 1], C), fontVariantNumeric: "tabular-nums" }}>띠 안의 점 <span style={{ color: 초 }}>{맞}</span> / 22 = 맞음</div>
    </AbsoluteFill>
  );
};

export const 점수72 = () => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const rows = [{ 이름: "칸 세기", 값: 0.6951, 색: 회 }, { 이름: "표면 거리", 값: 0.837, 색: 초 }], lo = 0.5, hi = 0.95, x0 = 300, 폭 = 600, 자 = (v: number) => x0 + 폭 * (v - lo) / (hi - lo);
  const 같 = spring({ frame: f - 60, fps, config: { stiffness: 260, damping: 15 } });
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      {rows.map((r, i) => { const s = 8 + i * 14, p = interpolate(f, [s, s + 30], [0, 1], { ...C, easing: 이징 }), y = 200 + i * 180;
        return <React.Fragment key={r.이름}>
          <div style={{ position: "absolute", left: 30, top: y, height: 110, display: "flex", alignItems: "center", fontSize: 42, color: 먹 }}>{r.이름}</div>
          <div style={{ position: "absolute", left: x0, top: y, width: (자(r.값) - x0) * p, height: 110, borderRadius: 14, background: r.색 }} />
          <div style={{ position: "absolute", left: x0 + (자(r.값) - x0) * p - 160, top: y, width: 150, height: 110, display: "flex", alignItems: "center", justifyContent: "flex-end", fontSize: 50, color: "white", fontVariantNumeric: "tabular-nums" }}>{(lo + (r.값 - lo) * p).toFixed(2)}</div>
        </React.Fragment>; })}
      <div style={{ position: "absolute", left: 0, top: 570, width: 1000, textAlign: "center", fontSize: 44, color: 금, opacity: Math.min(Math.max(같, 0) * 2, 1), scale: `${interpolate(같, [0, 1], [1.3, 1])}` }}>같은 모델 · 같은 답</div>
    </AbsoluteFill>
  );
};

// 실제 부품: 정답 · 틀 · 모델 셋이 차례로 올라옴 · F 숫자 · 표시(동그라미)
const 부품 = ({ 이름, 틀F, 모F, 표 }: { 이름: string; 틀F: number; 모F: number; 표?: { x: number; y: number; w: number; h: number; 색: string } }) => {
  const f = useCurrentFrame();
  const 칸 = [{ 글: "정답", 파일: "truth", 색: 초, F: null as number | null }, { 글: "틀", 파일: "hull", 색: 회, F: 틀F }, { 글: "모델", 파일: "model", 색: 금, F: 모F }];
  const 손 = interpolate(f, [70, 95], [0, 1], { ...C, easing: Easing.inOut(Easing.quad) });
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      {칸.map((c, i) => { const s = 6 + i * 12, p = interpolate(f, [s, s + 22], [0, 1], { ...C, easing: 이징 }), x = 10 + i * 330;
        return <div key={c.글} style={{ position: "absolute", left: x, top: 120, width: 320, opacity: p, translate: `0px ${(1 - p) * 40}px` }}>
          <Img src={staticFile(`ep72/${이름}_${c.파일}.png`)} style={{ width: 320, height: 320 }} />
          <div style={{ textAlign: "center", fontSize: 44, color: c.색 }}>{c.글}</div>
          {c.F !== null && <div style={{ textAlign: "center", fontSize: 40, color: 먹, fontVariantNumeric: "tabular-nums" }}>F {(c.F * interpolate(f, [s + 10, s + 40], [0, 1], C)).toFixed(2)}</div>}
        </div>; })}
      {표 && <div style={{ position: "absolute", left: 표.x, top: 표.y, width: 표.w, height: 표.h }}><Circle progress={손} color={표.색} strokeWidth={7} padding={6} seed={5 + Math.floor(f / 3)} roughness={1.8}><div style={{ width: 표.w, height: 표.h }} /></Circle></div>}
    </AbsoluteFill>
  );
};
export const 톱니72 = () => <부품 이름="gear" 틀F={0.795} 모F={0.996} 표={{ x: 760, y: 165, w: 160, h: 110, 색: 초 }} />;
export const 판72 = () => <부품 이름="plate" 틀F={0.954} 모F={0.966} 표={{ x: 790, y: 250, w: 140, h: 90, 색: 빨 }} />;
export const 관72 = () => <부품 이름="tube" 틀F={0.459} 모F={0.206} 표={{ x: 690, y: 190, w: 280, h: 150, 색: 빨 }} />;
