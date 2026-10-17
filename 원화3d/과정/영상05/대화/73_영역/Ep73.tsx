import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Circle } from "@remotion/rough-notation";

// 73 편 — 판정기준64(영역마다 높이 하나) · 그림이 주인 · 턴테이블(48 장 · 150 프레임 한 바퀴) · 값: 관 0.69 → 0.98 · 기운 판 0.99 → 0.06 · 712 중 오름 114 · 망가짐 192
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
          <Img src={staticFile(`ep73/${부품}_${c.파일}/${i}.png`)} style={{ width: 폭, height: 폭 }} />
          {c.빈 && <div style={{ position: "absolute", left: 0, top: 폭 / 2 - 40, width: 폭, textAlign: "center", fontSize: 60, color: 빨 }}>사라짐</div>}
          {판들.length > 1 && <div style={{ textAlign: "center", fontSize: 46, color: c.색, marginTop: -16 }}>{c.글}</div>}
        </div>; })}
      {표들.map((t, k) => <div key={k} style={{ position: "absolute", left: t.x, top: t.y, width: t.w, height: t.h }}>
        <Circle progress={interpolate(f, [t.시작, t.시작 + 22], [0, 1], { ...C, easing: Easing.inOut(Easing.quad) })} color={t.색} strokeWidth={7} padding={6} seed={5 + Math.floor(f / 3)} roughness={1.8}><div style={{ width: t.w, height: t.h }} /></Circle></div>)}
    </AbsoluteFill>
  );
};
export const 관전73 = () => <돌림 부품="tube" 판들={[{ 파일: "before", 글: "AI 결과", 색: 금 }]} 표들={[{ x: 560, y: 120, w: 300, h: 420, 색: 빨, 시작: 50 }]} />;
export const 관후73 = () => <돌림 부품="tube" 판들={[{ 파일: "before", 글: "바꾸기 전", 색: 금 }, { 파일: "after", 글: "바꾼 뒤", 색: 파 }]} />;
export const 판후73 = () => <돌림 부품="slant" 판들={[{ 파일: "truth", 글: "정답", 색: 초 }, { 파일: "before", 글: "바꾸기 전", 색: 금 }, { 파일: "after", 글: "바꾼 뒤", 색: 파, 빈: true }]} />;

// 위 그림의 영역: 선 그림 → 닫힌 칸마다 색이 하나씩 차오름 → 「색 하나 = 높이 하나」
export const 영역73 = () => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const 덮 = interpolate(f, [25, 75], [0, 100], { ...C, easing: 이징 }), 글 = spring({ frame: f - 85, fps, config: { stiffness: 260, damping: 15 } });
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      <Img src={staticFile("ep73/영역/선.png")} style={{ position: "absolute", left: 60, top: 70, width: 500, height: 500 }} />
      <Img src={staticFile("ep73/영역/색.png")} style={{ position: "absolute", left: 60, top: 70, width: 500, height: 500, clipPath: `inset(0 ${100 - 덮}% 0 0)` }} />
      <div style={{ position: "absolute", left: 600, top: 150, width: 380, fontSize: 46, color: 먹, lineHeight: 1.4 }}>앞에서 본 도면</div>
      <div style={{ position: "absolute", left: 600, top: 260, width: 380, fontSize: 46, color: 파, lineHeight: 1.4, opacity: Math.min(Math.max(글, 0) * 2, 1), scale: `${interpolate(글, [0, 1], [1.3, 1])}` }}>선으로 막힌 칸<br />= 깊이 하나</div>
    </AbsoluteFill>
  );
};
// 단면: 살짝 꺾인 얇은 판(초록) · 영역에 높이 하나(파란 점선 · 가운데 높이) · 그 높이로 위아래를 깎으니 판이 거의 다 잘려 나감(빨강)
export const 단면73 = () => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const 판 = interpolate(f, [5, 25], [0, 1], C), 선 = interpolate(f, [35, 55], [0, 1], { ...C, easing: 이징 }), 잘 = interpolate(f, [65, 95], [0, 1], C), 도 = spring({ frame: f - 100, fps, config: { stiffness: 260, damping: 15 } });
  const y = (x: number) => 300 + (x < 500 ? (500 - x) * 0.16 : (x - 500) * 0.16) * -1 + 40;   // 가운데가 낮게 꺾인 판
  const 점 = Array.from({ length: 85 }).map((_, i) => 80 + i * 10), h = y(500) - 40;
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      <svg width={1000} height={700}>
        {점.slice(0, -1).map((x, i) => { const 남 = Math.abs(y(x) - (h + 40)) < 14; const 색 = 잘 > 0 && !남 ? `rgba(220,50,50,${1 - 0.8 * 잘})` : 초;
          return <line key={i} x1={x} y1={y(x)} x2={x + 10} y2={y(x + 10)} stroke={색} strokeWidth={16} opacity={판} />; })}
        <line x1={60} y1={h + 40} x2={60 + 880 * 선} y2={h + 40} stroke={파} strokeWidth={6} strokeDasharray="18 12" />
      </svg>
      <div style={{ position: "absolute", left: 60, top: 90, fontSize: 38, color: 초, opacity: 판 }}>━ 살짝 꺾인 얇은 판 (옆에서 자른 모습)</div>
      <div style={{ position: "absolute", left: 60, top: 145, fontSize: 38, color: 파, opacity: 선 }}>┅ 칸에 준 깊이 하나</div>
      <div style={{ position: "absolute", left: 0, top: 560, width: 1000, textAlign: "center", fontSize: 54, color: 빨, opacity: Math.min(Math.max(도, 0) * 2, 1), scale: `${interpolate(도, [0, 1], [1.4, 1])}` }}>깊이가 다른 곳은 다 깎여 나감</div>
    </AbsoluteFill>
  );
};
export const 셈73 = () => {
  const f = useCurrentFrame(); const p = interpolate(f, [8, 50], [0, 1], { ...C, easing: 이징 });
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      <div style={{ position: "absolute", left: 0, top: 70, width: 1000, textAlign: "center", fontSize: 40, color: 회 }}>시험 부품 712 개</div>
      {[{ n: 114, 글: "좋아짐", 색: 초, x: 70 }, { n: 192, 글: "망가짐", 색: 빨, x: 530 }].map((k) => <div key={k.글} style={{ position: "absolute", left: k.x, top: 200, width: 400, textAlign: "center", color: k.색 }}>
        <div style={{ fontSize: 190, lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>{Math.round(k.n * p)}</div><div style={{ fontSize: 60 }}>{k.글}</div></div>)}
    </AbsoluteFill>
  );
};
