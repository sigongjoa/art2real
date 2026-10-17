import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Circle } from "@remotion/rough-notation";

// 72 편 2 판 — 그림이 주인: 정답 · 모델 턴테이블(48 장 · 150 프레임에 한 바퀴 · 300 프레임 = 두 줄) · 숫자는 큰 글 하나만
const 먹 = "rgb(40,40,50)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(220,160,30)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);
type 표 = { x: number; y: number; w: number; h: number; 색: string; 시작: number };
const 돌림 = ({ 부품, 큰, 큰색 = 먹, 표들 = [], 하나 = false }: { 부품: string; 큰?: string; 큰색?: string; 표들?: 표[]; 하나?: boolean }) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const i = Math.floor((f % 150) / 150 * 48), 쌍 = [{ 글: "정답", 파일: "truth", 색: 초 }, { 글: "AI 결과", 파일: "model", 색: 금 }];
  const 뿅 = spring({ frame: f - 6, fps, config: { stiffness: 260, damping: 15 } });
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      {하나 && <div style={{ position: "absolute", left: 180, top: 20, width: 640 }}><Img src={staticFile(`ep72/${부품}_model/${String(i).padStart(2, "0")}.png`)} style={{ width: 640, height: 640 }} /></div>}
      {!하나 && 쌍.map((c, j) => { const p = interpolate(f, [j * 8, j * 8 + 20], [0, 1], { ...C, easing: 이징 });
        return <div key={c.글} style={{ position: "absolute", left: 15 + j * 490, top: 95, width: 480, opacity: p, translate: `0px ${(1 - p) * 40}px` }}>
          <Img src={staticFile(`ep72/${부품}_${c.파일}/${String(i).padStart(2, "0")}.png`)} style={{ width: 480, height: 480 }} />
          <div style={{ textAlign: "center", fontSize: 50, color: c.색, marginTop: -20 }}>{c.글}</div>
        </div>; })}
      {큰 && <div style={{ position: "absolute", left: 0, top: 18, width: 1000, textAlign: "center", fontSize: 64, color: 큰색, opacity: Math.min(Math.max(뿅, 0) * 2, 1), scale: `${interpolate(뿅, [0, 1], [1.4, 1])}` }}>{큰}</div>}
      {표들.map((t, k) => <div key={k} style={{ position: "absolute", left: t.x, top: t.y, width: t.w, height: t.h }}>
        <Circle progress={interpolate(f, [t.시작, t.시작 + 22], [0, 1], { ...C, easing: Easing.inOut(Easing.quad) })} color={t.색} strokeWidth={7} padding={6} seed={5 + Math.floor(f / 3)} roughness={1.8}><div style={{ width: t.w, height: t.h }} /></Circle></div>)}
    </AbsoluteFill>
  );
};
export const 판돌림72 = () => <돌림 부품="plate" 큰="점수 0.97 · 거의 만점" />;
export const 판표72 = () => <돌림 부품="plate" 하나 표들={[{ x: 260, y: 200, w: 480, h: 230, 색: 빨, 시작: 40 }]} />;
export const 톱니돌림72 = () => <돌림 부품="gear" 표들={[{ x: 600, y: 170, w: 300, h: 200, 색: 초, 시작: 40 }]} />;
export const 관돌림72 = () => <돌림 부품="tube" 표들={[{ x: 560, y: 180, w: 380, h: 280, 색: 빨, 시작: 40 }]} />;

// 판 단면: 정답 윗면(초록 직선) · 1 칸 띠 · 금색 출렁이는 AI 윗면이 왼쪽부터 그려지며 띠 안이라 초록으로 바뀜 → 「다 맞음」
export const 단면72 = () => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const 띠 = interpolate(f, [8, 26], [0, 1], { ...C, easing: 이징 }), 그림 = interpolate(f, [30, 80], [0, 1], C), 맞 = interpolate(f, [80, 95], [0, 1], C);
  const y0 = 330, 반 = 55, 출 = (x: number) => y0 + 34 * Math.sin(x / 23) * Math.sin(x / 71 + 1);
  const 점 = Array.from({ length: 121 }).map((_, i) => 80 + i * 7).filter((x) => x <= 80 + 840 * 그림);
  const 도장 = spring({ frame: f - 98, fps, config: { stiffness: 260, damping: 15 } });
  const 색 = `rgb(${220 + (40 - 220) * 맞},${160 + (160 - 160) * 맞},${30 + (80 - 30) * 맞})`;
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      <div style={{ position: "absolute", left: 80, top: y0 - 반 * 띠, width: 840, height: 2 * 반 * 띠, background: "rgba(40,160,80,0.22)", border: `4px dashed ${초}`, boxSizing: "border-box", borderRadius: 10, zIndex: 1 }} />
      <div style={{ position: "absolute", left: 80, top: y0 + 2, width: 840, height: 220, background: "rgb(222,222,230)" }} />
      <div style={{ position: "absolute", left: 80, top: y0 - 4, width: 840, height: 8, background: 초 }} />
      <svg width={1000} height={700} style={{ position: "absolute" }}><polyline points={점.map((x) => `${x},${출(x)}`).join(" ")} fill="none" stroke={색} strokeWidth={9} strokeLinejoin="round" /></svg>
      <div style={{ position: "absolute", left: 80, top: 120, fontSize: 38, color: 초, opacity: 띠 }}>━ 정답 판 윗면 · 옅은 띠 = 이만큼은 맞음</div>
      <div style={{ position: "absolute", left: 80, top: 175, fontSize: 38, color: 금, opacity: interpolate(f, [30, 40], [0, 1], C) }}>〰 AI 결과 윗면</div>
      <div style={{ position: "absolute", left: 0, top: 575, width: 1000, textAlign: "center", fontSize: 60, color: 초, opacity: Math.min(Math.max(도장, 0) * 2, 1), scale: `${interpolate(도장, [0, 1], [1.4, 1])}` }}>출렁여도 띠 안 → 다 맞음</div>
    </AbsoluteFill>
  );
};
