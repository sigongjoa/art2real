import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Circle } from "@remotion/rough-notation";

// 75 편 — 판정기준69(깊이 32 단계) · 그림이 주인 · 턴테이블 · 값: 관 F 0.69 → 0.92 · 450 울퉁 6.8 → 5.8 % · F 0.906 → 0.907
const 먹 = "rgb(40,40,50)", 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(220,160,30)", 파 = "rgb(60,120,200)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);
type 판 = { 파일: string; 글: string; 색: string; 빈?: boolean };
type 표 = { x: number; y: number; w: number; h: number; 색: string; 시작: number };
const 돌림 = ({ 부품, 판들, 표들 = [] }: { 부품: string; 판들: 판[]; 표들?: 표[] }) => {
  const f = useCurrentFrame(); const i = String(Math.floor((f % 150) / 150 * 48)).padStart(2, "0");
  const 폭 = 판들.length === 1 ? 620 : 판들.length === 2 ? 480 : 330, 왼 = (1000 - 폭 * 판들.length) / 2;
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      {판들.map((c, j) => { const p = interpolate(f, [j * 10, j * 10 + 20], [0, 1], { ...C, easing: 이징 });
        return <div key={c.파일} style={{ position: "absolute", left: 왼 + j * 폭, top: 판들.length === 1 ? 10 : 90, width: 폭, opacity: p, translate: `0px ${(1 - p) * 40}px` }}>
          <Img src={staticFile(`ep75/${부품}_${c.파일}/${i}.png`)} style={{ width: 폭, height: 폭 }} />
          {c.빈 && <div style={{ position: "absolute", left: 0, top: 폭 / 2 - 40, width: 폭, textAlign: "center", fontSize: 60, color: 빨 }}>사라짐</div>}
          {판들.length > 1 && <div style={{ textAlign: "center", fontSize: 46, color: c.색, marginTop: -16 }}>{c.글}</div>}
        </div>; })}
      {표들.map((t, k) => <div key={k} style={{ position: "absolute", left: t.x, top: t.y, width: t.w, height: t.h }}>
        <Circle progress={interpolate(f, [t.시작, t.시작 + 22], [0, 1], { ...C, easing: Easing.inOut(Easing.quad) })} color={t.색} strokeWidth={7} padding={6} seed={5 + Math.floor(f / 3)} roughness={1.8}><div style={{ width: t.w, height: t.h }} /></Circle></div>)}
    </AbsoluteFill>
  );
};
export const 관전75 = () => <돌림 부품="tube" 판들={[{ 파일: "l16", 글: "AI 결과", 색: 금 }]} 표들={[{ x: 520, y: 110, w: 340, h: 440, 색: 빨, 시작: 50 }]} />;
export const 관비교75 = () => <돌림 부품="tube" 판들={[{ 파일: "truth", 글: "정답", 색: 초 }, { 파일: "l16", 글: "16 계단", 색: 금 }, { 파일: "l32", 글: "32 계단", 색: 파 }]} />;
export const 판비교75 = () => <돌림 부품="plate" 판들={[{ 파일: "truth", 글: "정답", 색: 초 }, { 파일: "l16", 글: "16 계단", 색: 금 }, { 파일: "l32", 글: "32 계단", 색: 파 }]} 표들={[{ x: 690, y: 140, w: 290, h: 220, 색: 빨, 시작: 50 }]} />;
// 계단: 비스듬한 정답 면(초록 선) 아래를 깊이 계단으로 깎은 모습 · 16 → 32 로 칸이 두 배
const 계단 = ({ n, 색 }: { n: number; 색: string }) => {
  const f = useCurrentFrame(); const p = interpolate(f, [6, 50], [0, 1], { ...C, easing: 이징 }); const x0 = 90, x1 = 910, y0 = 560, y1 = 170, 깊 = (x: number) => y0 - (y0 - y1) * (x - x0) / (x1 - x0);
  const 칸 = (y0 - y1) / n; const 보 = Math.floor(n * p);
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    <svg width={1000} height={700}>
      {Array.from({ length: 보 }).map((_, i) => { const yt = y0 - (i + 1) * 칸, xa = x0 + (x1 - x0) * (i * 칸) / (y0 - y1), xb = x0 + (x1 - x0) * ((i + 1) * 칸) / (y0 - y1);
        return <rect key={i} x={xa} y={yt} width={x1 - xa} height={칸} fill={색} fillOpacity={0.55} stroke={색} strokeWidth={1.5} />; })}
      <line x1={x0} y1={y0} x2={x1} y2={y1} stroke={초} strokeWidth={7} />
    </svg>
    <div style={{ position: "absolute", left: 70, top: 70, fontSize: 40, color: 초 }}>━ 정답 면 (비스듬)</div>
    <div style={{ position: "absolute", left: 70, top: 125, fontSize: 40, color: 색 === 금 ? "rgb(170,120,20)" : 파 }}>■ 깊이 {n} 계단으로 깎은 모습</div>
  </AbsoluteFill>;
};
export const 계단16 = () => <계단 n={16} 색={금} />;
export const 계단32 = () => <계단 n={32} 색={파} />;
export const 숫자75 = () => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig(); const p = interpolate(f, [8, 40], [0, 1], { ...C, easing: 이징 });
  const 막 = (y: number, 이름: string, v: number, 색: string) => <><div style={{ position: "absolute", left: 40, top: y, height: 110, display: "flex", alignItems: "center", fontSize: 44, color: 먹 }}>{이름}</div>
    <div style={{ position: "absolute", left: 300, top: y, width: 620 * (v / 8) * p, height: 110, borderRadius: 14, background: 색 }} />
    <div style={{ position: "absolute", left: 300 + 620 * (v / 8) * p + 14, top: y, height: 110, display: "flex", alignItems: "center", fontSize: 52, color: 색 }}>{(v * p).toFixed(1)} %</div></>;
  const 글 = spring({ frame: f - 50, fps, config: { stiffness: 260, damping: 15 } });
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    <div style={{ position: "absolute", left: 0, top: 60, width: 1000, textAlign: "center", fontSize: 40, color: 회 }}>평평해야 할 곳이 꺾인 비율 · 부품 450 개</div>
    {막(180, "16 계단", 6.8, 금)}{막(340, "32 계단", 5.8, 파)}
    <div style={{ position: "absolute", left: 0, top: 540, width: 1000, textAlign: "center", fontSize: 54, color: 초, opacity: Math.min(Math.max(글, 0) * 2, 1) }}>정답과 겹치는 점수는 그대로</div></AbsoluteFill>;
};
